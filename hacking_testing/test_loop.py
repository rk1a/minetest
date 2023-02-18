#!/usr/bin/env python3
from minetest_env import Minetest

env = Minetest(
    seed=42,
    start_minetest=True,
    xvfb_headless=True,
    sync_port=30010,
    sync_dtime=0.05,
)

render = False
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
