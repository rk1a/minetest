import datetime
import logging
import os
import random
import shutil
import subprocess
import uuid
from typing import Any, Dict, Optional, Tuple

import gym
import matplotlib.pyplot as plt
import numpy as np
import zmq
from proto_python.client import dumb_inputs_pb2 as dumb_inputs
from proto_python.client import dumb_outputs_pb2 as dumb_outputs

KEYS = [
    "FORWARD",
    "BACKWARD",
    "LEFT",
    "RIGHT",
    "JUMP",
    "SNEAK",
    "DIG",  # left mouse
    "MIDDLE",  # middle mouse
    "PLACE",  # right mouse
    "DROP",
    "HOTBAR_NEXT",
    "HOTBAR_PREVIOUS",
    "SLOT1",
    "SLOT2",
    "SLOT3",
    "SLOT4",
    "SLOT5",
    "SLOT6",
    "SLOT7",
    "SLOT8",
    # these keys open the inventory/menu
    # "ESC",
    "INVENTORY",
    # "AUX1",
    # these keys lead to errors:
    # "CHAT", "CMD",
    # these keys are probably uninteresting
    # "zoom",
    # "autoforward",
    # "pitchmove",
    # "freemove",
    # "fastmove",
    # "noclip",
    # "screenshot",
]


def start_minetest_server(
    minetest_path: str = "bin/minetest",
    config_path: str = "minetest.conf",
    log_path: str = "log/{}.log",
    server_port: int = 30000,
    world_dir: str = "newworld",
):
    cmd = [
        minetest_path,
        "--server",
        "--world",
        world_dir,
        "--gameid",
        "minetest",  # TODO does this have to be unique?
        "--config",
        config_path,
        "--port",
        str(server_port),
    ]
    stdout_file = log_path.format("server_stdout")
    stderr_file = log_path.format("server_stderr")
    with open(stdout_file, "w") as out, open(stderr_file, "w") as err:
        server_process = subprocess.Popen(cmd, stdout=out, stderr=err)
    return server_process


def start_minetest_client(
    minetest_path: str = "bin/minetest",
    config_path: str = "minetest.conf",
    log_path: str = "log/{}.log",
    client_port: int = 5555,
    server_port: int = 30000,
    cursor_img: str = "cursors/mouse_cursor_white_16x16.png",
    client_name: str = "MinetestAgent",
):
    cmd = [
        minetest_path,
        "--name",
        client_name,
        "--password",
        "1234",
        "--address",
        "0.0.0.0",  # listen to all interfaces
        "--port",
        str(server_port),
        "--go",
        "--dumb",
        "--client-address",
        "tcp://localhost:" + str(client_port),
        "--record",
        "--noresizing",
        "--config",
        config_path,
    ]
    if cursor_img:
        cmd.extend(["--cursor-image", cursor_img])

    stdout_file = log_path.format("client_stdout")
    stderr_file = log_path.format("client_stderr")
    with open(stdout_file, "w") as out, open(stderr_file, "w") as err:
        client_process = subprocess.Popen(cmd, stdout=out, stderr=err)
    return client_process


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
    ):
        # Graphics settings
        self.display_size = display_size
        self.fov_y = fov
        self.fov_x = self.fov_y * self.display_size[0] / self.display_size[1]
        self.max_mouse_move_x = 180 / self.fov_x * self.display_size[0]
        self.max_mouse_move_y = 180 / self.fov_y * self.display_size[1]

        # Define action and observation space
        self.action_space = gym.spaces.Dict(
            {
                **{key.lower(): gym.spaces.Discrete(2) for key in KEYS},
                **{
                    "mouse": gym.spaces.Box(
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
        if minetest_executable is None:
            self.minetest_executable = os.path.join(self.root_dir, "bin", "minetest")
        if log_dir is None:
            self.log_dir = os.path.join(self.root_dir, "log")
        os.makedirs(self.log_dir, exist_ok=True)
        self.world_dir = world_dir
        self.config_path = config_path
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
        if seed:
            self.seed(seed)

        # Configure logging
        logging.basicConfig(
            filename=os.path.join(self.log_dir, f"env_{self.unique_env_id}.log"),
            filemode="a",
            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
            datefmt='%H:%M:%S',
            level=logging.DEBUG,
        )

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
            self.log_dir, f"{{}}_{reset_timestamp}_{self.unique_env_id}.log",
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
        self.client_process = start_minetest_client(
            self.minetest_executable,
            self.config_path,
            log_path,
            self.env_port,
            self.server_port,
            self.cursor_image_path,
        )

    def _delete_world(self):
        if self.world_dir is not None:
            if os.path.exists(self.world_dir):
                shutil.rmtree(self.world_dir)
        else:
            raise RuntimeError(
                "World directory was not set. Please, provide a world directory"
                "in the constructor or seed the environment!",
            )

    def _delete_config(self):
        if self.config_path is not None:
            if os.path.exists(self.config_path):
                os.remove(self.config_path)
        else:
            raise RuntimeError(
                "Minetest config path was not set. Please, provide a config path"
                "in the constructor or seed the environment!",
            )

    def _write_config(self):
        with open(self.config_path, "w") as config_file:
            # Update default settings
            config_file.write("mute_sound = true\n")
            config_file.write("show_debug = false\n")

            # Set display size
            config_file.write(f"screen_w = {self.display_size[0]}\n")
            config_file.write(f"screen_h = {self.display_size[1]}\n")

            # Set FOV
            config_file.write(f"fov = {self.fov_y}\n")

            # Seed the map generator
            if self.seed:
                config_file.write(f"fixed_map_seed = {self.seed}\n")

    def seed(self, seed: int):
        self.seed = seed

        # Create UUID from seed
        rnd = random.Random()
        rnd.seed(self.seed)
        self.unique_env_id = str(uuid.UUID(int=rnd.getrandbits(128), version=4))

        # If not set manually, world and config paths are based on UUID
        if self.world_dir is None:
            self.world_dir = os.path.join(self.root_dir, self.unique_env_id)
        if self.config_path is None:
            self.config_path = os.path.join(self.root_dir, f"{self.unique_env_id}.conf")
            self._write_config()
        # TODO seed used libraries, like numpy, pytorch etc.

    def _unpack_pb_obs(self, received_obs: str):
        pb_obs = dumb_outputs.OutputObservation()
        pb_obs.ParseFromString(received_obs)
        obs = np.frombuffer(pb_obs.data, dtype=np.uint8).reshape(
            pb_obs.height,
            pb_obs.width,
            3,
        )
        rew = pb_obs.reward
        # TODO receive etc.
        done = False
        info = {}
        return obs, rew, done, info

    def _pack_pb_action(self, action: Dict[str, Any]):
        pb_action = dumb_inputs.InputAction()
        pb_action.mouseDx, pb_action.mouseDy = action["mouse"]
        for key, v in action.items():
            if key == "mouse":
                continue
            pb_action.keyEvents.append(
                dumb_inputs.KeyboardEvent(
                    key=key,
                    eventType=dumb_inputs.PRESS if v else dumb_inputs.RELEASE,
                ),
            )
        return pb_action

    def reset(self):
        if self.reset_world:
            self._delete_world()
        self._reset_zmq()
        self._reset_minetest()

        # Receive initial observation
        logging.debug("Waiting for first obs...")
        byte_obs = self.socket.recv()
        obs, _, _, _ = self._unpack_pb_obs(byte_obs)
        self.last_obs = obs
        logging.debug("Received first obs: {}".format(obs.shape))
        return obs

    def step(self, action: Dict[str, Any]):
        # Send action
        logging.debug("Sending action: {}".format(action))
        pb_action = self._pack_pb_action(action)
        self.socket.send(pb_action.SerializeToString())

        # TODO more robust check for whether a server/client is alive while receiving observations
        for process in [self.server_process, self.client_process]:
            if process.poll() is not None:
                return self.last_obs, 0.0, True, {}

        # Receive observation
        logging.debug("Waiting for obs...")
        byte_obs = self.socket.recv()
        next_obs, rew, done, info = self._unpack_pb_obs(byte_obs)
        self.last_obs = next_obs
        logging.debug(f"Received obs - {next_obs.shape}; reward - {rew}")
        return next_obs, rew, done, info

    def render(self, render_mode: str = "human"):
        if render_mode is None:
            gym.logger.warn(
                "You are calling render method without specifying any render mode. "
                "You can specify the render_mode at initialization, "
                f'e.g. gym("{self.spec.id}", render_mode="rgb_array")',
            )
            return
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

    def close(self):
        if self.render_fig is not None:
            plt.close()
        if self.socket is not None:
            self.socket.close()
        if self.client_process is not None:
            self.client_process.kill()
        if self.server_process is not None:
            self.server_process.kill()
        if self.reset_world:
            self._delete_world()
        if self.clean_config:
            self._delete_config()
