#!/usr/bin/env python3
import datetime
import time

import matplotlib.pyplot as plt
from minetest_env import Minetest

headless = True
sync = True
sync_port = 30010
sync_dtime = 0.001

env = Minetest(
    seed=42,
    start_minetest=True,
    xvfb_headless=headless,
    clientmods=[],
    sync_port=sync_port,
    sync_dtime=sync_dtime,
)

render = False

obs = env.reset()
done = False
tot_time = 0
time_list = []
fps_list = []

while True:
    start = time.time()
    try:
        action = env.action_space.sample()
        obs, rew, done, info = env.step(action)
        if render:
            env.render()

        dtime = time.time() - start
        tot_time += dtime
        fps = 1/dtime
        print(f"Time = {tot_time:.2f}s, FPS = {fps:.2f}Hz")
        time_list.append(tot_time)
        fps_list.append(fps)
    except KeyboardInterrupt:
        break
env.close()

# Plot FPS over time
plt.figure()
plt.plot(time_list, fps_list)
plt.xlabel("time")
plt.ylabel("FPS")
if sync:
    plt.savefig(f"fps_testloop_sync_{'headless_' if headless else ''}dt{sync_dtime}.png")
else:
    plt.savefig(f"fps_testloop_async_{'headless' if headless else ''}.png")
plt.show()
