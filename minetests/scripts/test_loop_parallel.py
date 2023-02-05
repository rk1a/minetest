from typing import Any, Dict, Optional

from gym.wrappers import TimeLimit
from minetests.minetest_env import Minetest
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv

if __name__ == "__main__":

    def make_env(
        rank: int,
        seed: int = 0,
        max_steps: int = 1e9,
        env_kwargs: Optional[Dict[str, Any]] = None,
    ):
        env_kwargs = env_kwargs or {}

        def _init():
            # Make sure that each Minetest instance has
            # - different server and client ports
            # - different and deterministic seeds
            env = Minetest(
                env_port=5555 + rank,
                server_port=30000 + rank,
                seed=seed + rank,
                **env_kwargs,
            )
            env = TimeLimit(env, max_episode_steps=max_steps)
            return env

        return _init

    # Env settings
    seed = 42
    max_steps = 100
    env_kwargs = {"display_size": (600, 400), "fov": 72}

    # Create a vectorized environment
    num_envs = 2  # Number of envs to use (<= number of avail. cpus)
    vec_env_cls = SubprocVecEnv  # DummyVecEnv
    venv = vec_env_cls(
        [
            make_env(rank=i, seed=seed, max_steps=max_steps, env_kwargs=env_kwargs)
            for i in range(num_envs)
        ],
    )

    # Start loop
    render = False
    obs = venv.reset()
    done = [False] * num_envs
    while sum(done) != num_envs:
        print(f"Elapsed steps: {venv.get_attr('_elapsed_steps')}")
        actions = [venv.action_space.sample() for _ in range(num_envs)]
        obs, rew, done, info = venv.step(actions)
        if render:
            venv.render()
    venv.close()
