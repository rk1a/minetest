import gym
from minetester.minetest_env import Minetest  # noqa


TASKS = [("treechop", 0), ("treechop", 1)]


for task, version in TASKS:
    gym.register(
        f"minetester-{task}-v{version}",
        entry_point="minetester.minetest_env:Minetest",
        kwargs=dict(clientmods=[f"{task}_v{version}"])
    )
