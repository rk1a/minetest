"""Tests for utilities."""
import os
import tempfile

import pytest

from minetester.utils import read_config_file, write_config_file


@pytest.fixture
def minetest_config_path():
    """Creates path to test Minetest configuration."""
    return os.path.join("minetester", "tests", "test_data", "test_minetest.conf")


def test_read_write_config(minetest_config_path):
    """Test configuration reading and writing utils."""
    config = read_config_file(minetest_config_path)
    assert config["server_announce"] is True
    assert config["menu_last_game"] == "minetest"
    assert config["fps_max"] == 1000
    with tempfile.NamedTemporaryFile("w+") as f:
        write_config_file(f.name, config)
        assert os.path.exists(f.name)
        assert read_config_file(f.name) == config
