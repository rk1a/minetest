#!/usr/bin/env python3
from minetester import Minetest

env = Minetest(
    seed=42,
    start_minetest=True,
    xvfb_headless=True,
    clientmods=["random_v0"],
)

render = True
obs = env.reset()
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
