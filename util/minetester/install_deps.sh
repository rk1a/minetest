#!/bin/bash

# Get the operating system name
OS=$(lsb_release -si)

# Check if the OS is Ubuntu
if [ "$OS" == "Ubuntu" ]; then
    # If it's Ubuntu, execute the command
    echo "You are running Ubuntu. Executing command..."
    sudo apt-get install xvfb g++ make libzmq3-dev libtool pkg-config build-essential autoconf automake libc6-dev cmake libpng-dev libjpeg-dev libxi-dev libgl1-mesa-dev libsqlite3-dev libogg-dev libvorbis-dev libopenal-dev libcurl4-gnutls-dev libfreetype6-dev zlib1g-dev libgmp-dev libjsoncpp-dev libzstd-dev libluajit-5.1-dev protobuf-compiler patchelf
elif [ "$OS" == "Arch" ]; then
    echo "You are running Arch. Executing command..."
    sudo pacman -S base-devel libcurl-gnutls cmake libxi libpng sqlite libogg libvorbis openal freetype2 jsoncpp gmp luajit leveldb ncurses zstd gettext
else
    # If it's not Ubuntu, print a message and exit
    echo "This script only works on Ubuntu or Arch. See https://github.com/minetest/minetest/blob/master/doc/compiling/linux.md for instructions on installing your necessary dependencies. Exiting."
    exit 1
fi
