-- set random reward at every step
minetest.register_globalstep(function(dtime)
    reward = math.random()
end)