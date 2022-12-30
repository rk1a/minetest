from minetest_env import Minetest

start_minetest = True
render = False
seed = 42
env = Minetest(seed=seed, start_minetest=start_minetest)
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
