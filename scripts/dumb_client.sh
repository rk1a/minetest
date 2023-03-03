#!/bin/bash
exec bin/minetest --name MinetestAgent --password whyisthisnecessary --address 0.0.0.0 --port 30000 --sync-port 30010 --go --dumb --client-address "tcp://localhost:5555" --record --noresizing --cursor-image "cursors/mouse_cursor_white_16x16.png" --headless
