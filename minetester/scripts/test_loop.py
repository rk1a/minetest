#!/usr/bin/env python3
"""Test loop for Minetest environment."""
from minetester import Minetest

if __name__ == "__main__":
    env = Minetest(
        seed=42,
        start_minetest=True,
        sync_port=30010,
        sync_dtime=0.05,
        headless=True,
        start_xvfb=True,
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
