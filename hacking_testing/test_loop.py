#!/usr/bin/env python
from minetest_env import Minetest

env = Minetest()
obs = env.reset()
render = False
done = False
while not done:
    try:
        action = env.action_space.sample()
        obs, rew, done, info = env.step(action)
        if render:
            env.render()
    except KeyboardInterrupt:
        break
env.close()
