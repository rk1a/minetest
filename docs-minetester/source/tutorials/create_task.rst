How to create a new task?
================================

Tasks are easy to create using Minetest's builtin Lua modding API. 
The task-relevant information (rewards, task completion status, meta information, ...) are passed through the Minetest processes and made available to the `client API <client_api.html>`_.


Task definition
---------------

A basic Minetest mod is defined by a directory with the following structure

.. code-block::

    my_task\
        mod.conf
        init.lua
        settingtypes.txt

where `mod.conf` contains meta data, `init.lua` the necessary Lua code, and `settingtypes.txt` possible mod settings.

A task has to define two global variables in the Lua script environment:

1. `REWARD`: a scalar floting point number indicating the reward received at the current step.
2. `TERMINAL`: a boolean indicating whether the agent has reached a terminal state of the task.

The variables can be changed at every step, or based on in-game events.

Example: A simple treechop task
-------------------------------

`mod.conf`

.. code-block::

    name=treechop

`settingtypes.txt`

.. code-block::

    #    Number of tree chops required for completing task
    #    Default is 10. At least one chop is required.
    treechop_goal (Tree chop goal) int 10 1 65535


`ìnit.lua`

.. code-block:: lua

    -- task settings
    TREECHOP_GOAL = minetest.settings:get("treechop_goal") or 10

    minetest.register_on_dignode(function(pos, node, digger)
        if string.find(node["name"], "tree") then
            minetest.debug("Dug a tree!")
            REWARD[digger:get_player_name()] = 1.0
        end

        -- count the number of tree items of digging player
        local num_tree_items = 0
        local inv = digger:get_inventory()
        local size = inv:get_size("main")
        for i = 1, size do
            local stack = inv:get_stack("main", i)
            if string.find(stack:get_name(), "tree") then
                    num_tree_items = num_tree_items + stack:get_count()
            end
        end
        if num_tree_items >= TREECHOP_GOAL then
                minetest.debug(digger:get_player_name() .. " reached the goal!")
                TERMINAL[digger:get_player_name()] = true
        end
    end)


Asynchronous mode and client mods
---------------------------------

Currently, server mods can only be used to modify the Minetester global variables if client-server synchronization is active.
Otherwise, a client mod has to be used instead.
Client mods have certain limitations to what information they can access. 
For example, there is no acces to a player's inventory.
To circumvent these limitations, one can use a pair of mods (one client and one server mod) that establish a mod channel between them to share the missing information.
However, it is recommended to use client-server synchronization with a single server mod where possible.

Further resources
-----------------

- `Minetest Modding API Reference <https://minetest.gitlab.io/minetest/>`_
- `Minetest Modding Forum <https://forum.minetest.net/viewforum.php?f=46&sid=c43ec11858a985a18618026196a4d794>`_