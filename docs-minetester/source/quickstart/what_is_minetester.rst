What is Minetester?
===================

Minetester extends the open-source voxel engine `Minetest <https://www.minetest.net/>`_ to support training and evaluation of AI / RL agents.
The Minetest core was modified to add the following main features:

- a dummy client that adds an `API for controlling a player and receiving game information <../tutorials/client_api.html>`_
- support for `custom tasks using the Minetest modding API <../tutorials/create_task.html>`_
- headless client operation
- client-server synchronization

In addition, the *minetester* Python package provides a gymnasium environment and utilities for communication with Minetest clients.