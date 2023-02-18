minetest.register_on_dignode(function(pos, node, digger)
   if string.find(node["name"], "tree") then
        REWARD[digger:get_player_name()] = 1.0
        minetest.debug("Dug a tree!")
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