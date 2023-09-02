import gymnasium as gym
from gymnasium.utils.env_checker import check_env

env = gym.make("Minetest-v0")

check_env(env.unwrapped)