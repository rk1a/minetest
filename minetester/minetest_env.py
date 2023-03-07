import datetime
import logging
import os
import random
import shutil
import uuid
from typing import Any, Dict, List, Optional, Tuple

import gym
import matplotlib.pyplot as plt
import numpy as np
import psutil
import zmq
from minetester.utils import (KEY_MAP, pack_pb_action, start_minetest_client,
                              start_minetest_server, unpack_pb_obs)


class Minetest(gym.Env):
    metadata = {"render.modes": ["rgb_array", "human"]}

    def __init__(
        self,
        env_port: int = 5555,
        server_port: int = 30000,
        minetest_executable: Optional[os.PathLike] = None,
        log_dir: Optional[os.PathLike] = None,
        config_path: Optional[os.PathLike] = None,
        cursor_image_path: Optional[os.PathLike] = None,
        world_dir: Optional[os.PathLike] = None,
        display_size: Tuple[int, int] = (1024, 600),
        fov: int = 72,
        seed: Optional[int] = None,
        start_minetest: bool = True,
        clientmods: List[str] = [],
        servermods: List[str] = [],
        config_dict: Dict[str, Any] = {},
        xvfb_headless: bool = False,
    ):
        # Graphics settings
        self.xvfb_headless = xvfb_headless
        self.display_size = display_size
        self.fov_y = fov
        self.fov_x = self.fov_y * self.display_size[0] / self.display_size[1]
        # Define action and observation space
        self.max_mouse_move_x = self.display_size[0]
        self.max_mouse_move_y = self.display_size[1]
        self.action_space = gym.spaces.Dict(
            {
                **{key: gym.spaces.Discrete(2) for key in KEY_MAP.keys()},
                **{
                    "MOUSE": gym.spaces.Box(
                        np.array([-self.max_mouse_move_x, -self.max_mouse_move_y]),
                        np.array([self.max_mouse_move_x, self.max_mouse_move_y]),
                        shape=(2,),
                        dtype=int,
                    ),
                },
            },
        )
        self.observation_space = gym.spaces.Box(
            0,
            255,
            shape=(self.display_size[1], self.display_size[0], 3),
            dtype=np.uint8,
        )

        # Define Minetest paths
        self.root_dir = os.path.dirname(os.path.dirname(__file__))
        self.minetest_executable = minetest_executable
        if minetest_executable is None:
            self.minetest_executable = os.path.join(self.root_dir, "bin", "minetest")
        if log_dir is None:
            self.log_dir = os.path.join(self.root_dir, "log")
        os.makedirs(self.log_dir, exist_ok=True)
        self.world_dir = world_dir
        self.config_path = config_path
        self.cursor_image_path = cursor_image_path
        if cursor_image_path is None:
            self.cursor_image_path = os.path.join(
                self.root_dir,
                "cursors",
                "mouse_cursor_white_16x16.png",
            )

        # Regenerate and clean world if no custom world provided
        self.reset_world = self.world_dir is None

        # Clean config if no custom config provided
        self.clean_config = self.config_path is None

        # Whether to start minetest server and client
        self.start_minetest = start_minetest

        # Used ports
        self.env_port = env_port  # MT env <-> MT client
        self.server_port = server_port  # MT client <-> MT server

        # ZMQ objects
        self.socket = None
        self.context = None

        # Minetest processes
        self.server_process = None
        self.client_process = None

        # Env objects
        self.last_obs = None
        self.render_fig = None
        self.render_img = None

        # Seed the environment
        self.unique_env_id = str(uuid.uuid4())  # fallback UUID when no seed is provided
        if seed is not None:
            self.seed(seed)

        # Configure logging
        logging.basicConfig(
            filename=os.path.join(self.log_dir, f"env_{self.unique_env_id}.log"),
            filemode="a",
            format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
            datefmt="%H:%M:%S",
            level=logging.DEBUG,
        )

        # Configure mods
        self.clientmods = clientmods + ["rewards"]  # require the base rewards mod
        # add client mod names in case they entail a server side component
        self.servermods = servermods + clientmods
        self._enable_clientmods()
        self._enable_servermods()

        # Write minetest.conf
        self.config_dict = config_dict
        self._write_config()

    def _enable_clientmods(self):
        clientmods_folder = os.path.realpath(
            os.path.join(os.path.dirname(self.minetest_executable), "../clientmods"),
        )
        if not os.path.exists(clientmods_folder):
            raise RuntimeError(f"Client mods must be located at {clientmods_folder}!")
        # Write mods.conf to enable client mods
        with open(os.path.join(clientmods_folder, "mods.conf"), "w") as mods_config:
            for clientmod in self.clientmods:
                clientmod_folder = os.path.join(clientmods_folder, clientmod)
                if not os.path.exists(clientmod_folder):
                    logging.warning(
                        f"Client mod {clientmod} was not found!"
                        " It must be located at {clientmod_folder}.",
                    )
                else:
                    mods_config.write(f"load_mod_{clientmod} = true\n")

    def _enable_servermods(self):
        # Check if there are any server mods
        servermods_folder = os.path.realpath(
            os.path.join(os.path.dirname(self.minetest_executable), "../mods"),
        )
        if not os.path.exists(servermods_folder):
            raise RuntimeError(f"Server mods must be located at {servermods_folder}!")
        # Create world_dir/worldmods folder
        self._check_world_dir()
        worldmods_folder = os.path.join(self.world_dir, "worldmods")
        os.makedirs(worldmods_folder, exist_ok=True)
        # Copy server mods to world_dir/worldmods
        for mod in self.servermods:
            mod_folder = os.path.join(servermods_folder, mod)
            world_mod_folder = os.path.join(worldmods_folder, mod)
            if not os.path.exists(mod_folder):
                logging.warning(
                    f"Server mod {mod} was not found!"
                    f" It must be located at {mod_folder}.",
                )
            else:
                shutil.copytree(mod_folder, world_mod_folder)

    def _reset_zmq(self):
        if self.socket:
            self.socket.close()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://*:{self.env_port}")

    def _reset_minetest(self):
        # Determine log paths
        reset_timestamp = datetime.datetime.now().strftime("%m-%d-%Y,%H:%M:%S")
        log_path = os.path.join(
            self.log_dir,
            f"{{}}_{reset_timestamp}_{self.unique_env_id}.log",
        )

        # (Re)start Minetest server
        if self.server_process:
            self.server_process.kill()

        self.server_process = start_minetest_server(
            self.minetest_executable,
            self.config_path,
            log_path,
            self.server_port,
            self.world_dir,
        )

        # (Re)start Minetest client
        if self.client_process:
            self.client_process.kill()
            if self.xvfb_headless:
                # kill running xvfb processes
                for proc in psutil.process_iter():
                    if proc.name() in ["Xvfb"]:
                        proc.kill()
        self.client_process = start_minetest_client(
            self.minetest_executable,
            self.config_path,
            log_path,
            self.env_port,
            self.server_port,
            self.cursor_image_path,
            xvfb_headless=self.xvfb_headless,
        )
    
    def _check_world_dir(self):
        if self.world_dir is None:
            raise RuntimeError(
                "World directory was not set. Please, provide a world directory "
                "in the constructor or seed the environment!",
            )

    def _delete_world(self):
        self._check_world_dir()
        if os.path.exists(self.world_dir):
            shutil.rmtree(self.world_dir)
    
    def _check_config_path(self):
        if self.config_path is None:
            raise RuntimeError(
                "Minetest config path was not set. Please, provide a config path "
                "in the constructor or seed the environment!",
            )

    def _delete_config(self):
        self._check_config_path()
        if os.path.exists(self.config_path):
            os.remove(self.config_path)

    def _write_config(self):
        with open(self.config_path, "w") as config_file:
            # Update default settings
            config_file.write("mute_sound = true\n")
            config_file.write("show_debug = false\n")
            config_file.write("enable_client_modding = true\n")
            config_file.write("csm_restriction_flags = 0\n")
            config_file.write("enable_mod_channels = true\n")

            # Set display size
            config_file.write(f"screen_w = {self.display_size[0]}\n")
            config_file.write(f"screen_h = {self.display_size[1]}\n")

            # Set FOV
            config_file.write(f"fov = {self.fov_y}\n")

            # Seed the map generator
            if self.the_seed:
                config_file.write(f"fixed_map_seed = {self.the_seed}\n")

            # Set from custom config dict
            for key, value in self.config_dict.items():
                config_file.write(f"{key} = {value}\n")

    def seed(self, seed: int):
        self.the_seed = seed

        # Create UUID from seed
        rnd = random.Random()
        rnd.seed(self.the_seed)
        self.unique_env_id = str(uuid.UUID(int=rnd.getrandbits(128), version=4))

        # If not set manually, world and config paths are based on UUID
        if self.world_dir is None:
            self.world_dir = os.path.join(self.root_dir, self.unique_env_id)
        if self.config_path is None:
            self.config_path = os.path.join(self.root_dir, f"{self.unique_env_id}.conf")

    def reset(self):
        if self.start_minetest:
            if self.reset_world:
                self._delete_world()
            self._enable_servermods()
            self._reset_minetest()
        self._reset_zmq()

        # Receive initial observation
        logging.debug("Waiting for first obs...")
        byte_obs = self.socket.recv()
        obs, _, _, _, _ = unpack_pb_obs(byte_obs)
        self.last_obs = obs
        logging.debug("Received first obs: {}".format(obs.shape))
        return obs

    def step(self, action: Dict[str, Any]):
        # Send action
        if isinstance(action["MOUSE"], np.ndarray):
            action["MOUSE"] = action["MOUSE"].tolist()
        logging.debug("Sending action: {}".format(action))
        pb_action = pack_pb_action(action)
        self.socket.send(pb_action.SerializeToString())

        # TODO more robust check for whether a server/client is alive while receiving observations
        for process in [self.server_process, self.client_process]:
            if process is not None and process.poll() is not None:
                return self.last_obs, 0.0, True, {}

        # Receive observation
        logging.debug("Waiting for obs...")
        byte_obs = self.socket.recv()
        next_obs, rew, done, info, last_action = unpack_pb_obs(byte_obs)

        if last_action:
            assert action == last_action

        self.last_obs = next_obs
        logging.debug(f"Received obs - {next_obs.shape}; reward - {rew}")
        return next_obs, rew, done, info

    def render(self, render_mode: str = "human"):
        if render_mode == "human":
            if self.render_img is None:
                # Setup figure
                plt.rcParams["toolbar"] = "None"
                plt.rcParams["figure.autolayout"] = True

                self.render_fig = plt.figure(
                    num="Minetest Env",
                    figsize=(3 * self.display_size[0] / self.display_size[1], 3),
                )
                self.render_img = self.render_fig.gca().imshow(self.last_obs)
                self.render_fig.gca().axis("off")
                self.render_fig.gca().margins(0, 0)
                self.render_fig.gca().autoscale_view()
            else:
                self.render_img.set_data(self.last_obs)
            plt.draw(), plt.pause(1e-3)
        elif render_mode == "rgb_array":
            return self.last_obs
        else:
            raise NotImplementedError(
                "You are calling 'render()' with an unsupported"
                f" render mode: '{render_mode}'. "
                f"Supported modes: {self.metadata['render.modes']}"
            )

    def close(self):
        if self.render_fig is not None:
            plt.close()
        if self.socket is not None:
            self.socket.close()
        # TODO improve process termination
        # i.e. don't kill, but close signal
        if self.client_process is not None:
            self.client_process.kill()
        if self.server_process is not None:
            self.server_process.kill()
        if self.xvfb_headless:
            # kill remaining xvfb and minetest processes
            for proc in psutil.process_iter():
                if proc.name() in ["Xvfb", "minetest"]:
                    proc.kill()
        if self.reset_world:
            self._delete_world()
        if self.clean_config:
            self._delete_config()
