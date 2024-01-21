"""Tests for Minetest environment."""
import random
from typing import Any, Dict

import numpy as np
import pytest
from gymnasium.vector import AsyncVectorEnv
from gymnasium.wrappers import TimeLimit

from minetester import Minetest
from minetester.utils import start_xserver


@pytest.fixture
def unused_display():
    """Create unique display variable."""
    base_display = 2
    unused_display.counter = getattr(unused_display, "counter", 0) + 1
    display = base_display + unused_display.counter
    return display


@pytest.fixture(params=["sdl2", "xvfb"])
def minetest_env(unused_tcp_port_factory, unused_display, request):
    """Create Minetest environment."""
    env_port, server_port = unused_tcp_port_factory(), unused_tcp_port_factory()
    headless, start_xvfb = (True, True) if request.param == "xvfb" else (True, False)
    mt = Minetest(
        env_port=env_port,
        server_port=server_port,
        base_seed=42,
        headless=headless,
        start_xvfb=start_xvfb,
        x_display=unused_display,
    )
    print(mt.env_port, mt.server_port, mt.x_display)
    yield mt
    mt.close()


def test_reset_step_returns(minetest_env):
    """Test reset and step return types."""
    obs, info = minetest_env.reset()
    assert isinstance(obs, np.ndarray)
    assert isinstance(info, dict)
    action = minetest_env.action_space.sample()
    assert isinstance(action, dict) and all(
        isinstance(key, str) and isinstance(value, (int, np.int64, np.ndarray))
        for key, value in action.items()
    )
    obs, rew, done, truncated, info = minetest_env.step(action)
    assert isinstance(obs, np.ndarray)
    assert isinstance(rew, float)
    assert isinstance(done, bool)
    assert isinstance(truncated, bool)
    assert isinstance(info, dict)


def test_loop(minetest_env):
    """Execution test of step-action-loop."""
    max_steps = 10
    minetest_env = TimeLimit(minetest_env, max_episode_steps=max_steps)
    minetest_env.reset()
    done, truncated = False, False
    while not (done or truncated):
        action = minetest_env.action_space.sample()
        _, _, done, truncated, _ = minetest_env.step(action)


def test_loop_parallel(unused_display, unused_tcp_port_factory):
    """Execution test of parallel step-action-loops."""

    def _make_env(
        rank: int,
        seed: int,
        max_steps: int,
        env_kwargs: Dict[str, Any],
    ):
        def _init():
            # Make sure that each Minetest instance has
            # - different server and client ports
            # - different and seeds
            env_port, server_port = unused_tcp_port_factory(), unused_tcp_port_factory()
            env = Minetest(
                env_port=env_port,
                server_port=server_port,
                base_seed=seed + rank,
                **env_kwargs,
            )
            print(env.env_port, env.server_port, env.x_display)
            # Assign random timelimit to check that resets work properly
            env = TimeLimit(
                env,
                max_episode_steps=random.randint(max_steps // 2, max_steps),
            )
            return env

        return _init

    # Env settings
    seed = 42
    max_steps = 20
    x_display = unused_display
    env_kwargs = {
        "display_size": (600, 400),
        "fov": 72,
        "headless": True,
        "x_display": x_display,
    }

    # Create a vectorized environment
    num_envs = 2  # Number of envs to use (<= number of avail. cpus)
    vec_env_cls = AsyncVectorEnv
    venv = vec_env_cls(
        [
            _make_env(rank=i, seed=seed, max_steps=max_steps, env_kwargs=env_kwargs)
            for i in range(num_envs)
        ],
    )

    # Start loop
    xserver = start_xserver(x_display)
    venv.reset()
    step = 0
    while step < max_steps:
        actions = venv.action_space.sample()
        venv.step(actions)
        step += 1
    venv.close()
    xserver.terminate()
