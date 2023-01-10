
reward = 0.0

-- reset reward every step
minetest.register_globalstep(function(dtime)
    reward = 0.0
end)

-- reward chopping tree nodes
minetest.register_on_dignode(function(pos, node)
    if string.find(node["name"], "tree") then
        reward = 1.0
    end
end)