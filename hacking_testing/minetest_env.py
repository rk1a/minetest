import gym
import zmq
from gym.spaces import Box, Dict, Discrete

KEYS = [
    "FORWARD",
    "BACKWARD",
    "LEFT",
    "RIGHT",
    "JUMP",
    "SNEAK",
    "DIG",  # left mouse
    "PLACE",   # right mouse
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
    # "INVENTORY",
    "AUX1",
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


class Minetest(gym.Env):
    def __init__(self, port: int = 5555):
        # Define action space
        self.action_space = Dict({
            **{key.lower(): Discrete(2) for key in KEYS},
            **{"mouse": Box(-11, 11, shape=(2,), dtype=int)},
        })
        # TODO define obs and reward space

        # Setup ZMQ
        self.port = port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://*:{self.port}")

    def reset(self):
        print("Waiting for obs...")
        obs = self.socket.recv()
        print("Received obs: {}".format(obs))
        return obs

    def step(self, action):
        print("Sending action: {}".format(action))
        # make mouse action serializable
        action["mouse"] = action["mouse"].tolist()
        self.socket.send_json(action)
        print("Waiting for obs...")
        next_obs = self.socket.recv()
        print("Received obs: {}".format(next_obs))
        # TODO receive rewards etc.
        rew = 0.
        done = False
        info = {}
        return next_obs, rew, done, info
