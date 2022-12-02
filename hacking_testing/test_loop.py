from minetest_env import Minetest

env = Minetest()
obs = env.reset()
render = False
done = False
while not done:
    action = env.action_space.sample()
    obs, rew, done, info = env.step(action)
    if render:
        env.render()
env.close()
