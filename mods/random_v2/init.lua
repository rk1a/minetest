minetest.register_globalstep(function(dtime)
   -- set a random reward and terminal value
   local players = minetest.get_connected_players() 
   for i = 1, #players do
      local playername = players[i]:get_player_name()
      minetest.debug("Reward before: " .. tostring(REWARD[playername]))
      REWARD[playername] = math.random()
      TERMINAL[playername] = math.floor(math.random() + 0.5) == 1
   end
end)