-- https://github.com/minetest/minetest/issues/10682
local function register_globalstep_on_mods_loaded(func)
    local function wrapper_func(dtime)
         if not minetest.localplayer then return end
         func(dtime)
         for i, globalstep in pairs(minetest.registered_globalsteps) do
              if globalstep == wrapper_func then
                  minetest.registered_globalsteps[i] = func
              end
         end
    end
    minetest.register_globalstep(wrapper_func)
end
reward = 0.0
-- local loaded = false
register_globalstep_on_mods_loaded(function()
    -- if(loaded) then return end
    -- loaded = true
    -- local channel_name = "rewards_"..minetest.localplayer:get_name()
    -- minetest.mod_channel_join(channel_name)
    -- minetest.register_on_modchannel_message(function(channel_name, sender, message) end)
    reward = math.random()
end)