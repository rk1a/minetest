-- define global reward and terminal variables
REWARD = 0.0
TERMINAL = false

-- reset reward every step
minetest.register_globalstep(function(dtime)
    REWARD = 0.0
end)
