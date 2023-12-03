minetest.register_globalstep(function(dtime)
    -- set a random reward and terminal value
    local players = minetest.get_connected_players()
    for i = 1, #players do
        local player = players[i]
        local playername = player:get_player_name()
        minetest.debug("Reward before: " .. tostring(REWARD[playername]))
        local reward = math.random()
        REWARD[playername] = reward
        TERMINAL[playername] = math.floor(reward + 0.05) == 1
        INFO[playername] = playername .. " is at " ..
                               tostring(player:get_pos())
    end
end)
