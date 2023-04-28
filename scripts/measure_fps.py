#!/usr/bin/env python3
import time

import matplotlib.pyplot as plt
import numpy as np
from minetester.minetest_env import Minetest

headless = True
render = False
sync = True
sync_port = 30010
sync_dtime = 0.05
undersampling = 1

env = Minetest(
    seed=42,
    start_minetest=True,
    xvfb_headless=headless,
    sync_port=sync_port,
    sync_dtime=sync_dtime,
    config_dict=dict(undersampling=undersampling),
)

obs = env.reset()
tot_time = 0
time_list = []
fps_list = []
step = 0
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
        time_list.append(tot_time)
        fps_list.append(fps)
        step += 1
    except KeyboardInterrupt:
        break
env.close()

# Print stats
fps_np = np.array(fps_list)
print(f"Runtime = {tot_time:.2f}s")
print(f"Avg. FPS = {fps_np.mean():.2f}, Min. FPS = {fps_np.min():.2f}, Max. FPS = {fps_np.max():.2f}")

# Plot FPS over time
plt.figure()
plt.plot(time_list, fps_list, label="data")
# Calculate moving average
window = int(len(fps_list) * 0.1) + 1
mav = np.convolve(fps_np, np.ones(window) / window, mode="same")
plt.plot(time_list, mav, label="moving avg.")
plt.xlabel("time [s]")
plt.ylabel("FPS")
plt.legend()
if sync:
    plt.savefig(f"fps_testloop_sync_{'headless_' if headless else ''}.png")
else:
    plt.savefig(f"fps_testloop_async_{'headless' if headless else ''}.png")
plt.show()
