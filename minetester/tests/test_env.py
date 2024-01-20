"""Tests for Minetest environment."""
import random
from typing import Any, Dict, Optional

import numpy as np
import pytest
from gymnasium.vector import AsyncVectorEnv
from gymnasium.wrappers import TimeLimit

from minetester import Minetest
from minetester.utils import start_xserver


@pytest.fixture
def unique_env_port():
    """Create unique environment ports."""
    base_port = 5555
    unique_env_port.counter = getattr(unique_env_port, "counter", 0) + 1
    port = base_port + unique_env_port.counter
    return port


@pytest.fixture
def unique_server_port():
    """Create unique server ports."""
    base_port = 30000
    unique_server_port.counter = getattr(unique_server_port, "counter", 0) + 1
    port = base_port + unique_server_port.counter
    return port


@pytest.fixture(params=["xvfb", "sdl2"])
def minetest_env(unique_env_port, unique_server_port, request):
    """Create Minetest environment."""
    headless, start_xvfb = (True, True) if request.param == "xvfb" else (True, False)
    mt = Minetest(
        env_port=unique_env_port,
        server_port=unique_server_port,
        base_seed=42,
        headless=headless,
        start_xvfb=start_xvfb,
    )
    yield mt
    mt.close()


def test_reset(minetest_env):
    """Tests reset return types."""
    obs, info = minetest_env.reset()
    assert isinstance(obs, np.ndarray)
    assert isinstance(info, dict)


def test_step(minetest_env):
    """Tests step return types."""
    obs, info = minetest_env.reset()
    action = minetest_env.action_space.sample()
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
        print(done, truncated)


def test_loop_parallel(unique_env_port, unique_server_port):
    """Execution test of parallel step-action-loops."""

    def _make_env(
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
                env_port=unique_env_port + rank,
                server_port=unique_server_port + rank,
                base_seed=seed + rank,
                **env_kwargs,
            )
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
    x_display = 4
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

    # Start X server
    xserver = start_xserver(x_display)

    # Start loop
    venv.reset()
    step = 0
    while step < max_steps:
        print(f"Elapsed steps: {venv.get_attr('_elapsed_steps')}")
        actions = venv.action_space.sample()
        venv.step(actions)
        step += 1
    venv.close()
    xserver.terminate()
