#!/bin/bash
exec bin/minetest --server --world newworld --gameid minetest --sync-port 30001 --sync-dtime 0.001 --config hacking_testing/minetest.conf
