-- define global reward variable
reward = 0.0

-- reset reward every step
minetest.register_globalstep(function(dtime)
    reward = 0.0
end)