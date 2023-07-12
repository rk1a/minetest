.PHONY: all deps repos sdl2 package zmqpp
SDL2_CMAKE_FILE := lib/SDL/build/lib/cmake/SDL2/sdl2-config.cmake
ZMQPP_LIB_FILE := lib/zmqpp/build/max-g++/libzmqpp.a

all: package

deps:
	# Install dependencies
	util/minetester/install_deps.sh

repos:
	# Init all submodules
	git submodule update --init --recursive

$(SDL2_CMAKE_FILE): repos
	# compile sdl2
	util/minetester/build_sdl2.sh

sdl2: $(SDL2_CMAKE_FILE)

$(ZMQPP_LIB_FILE): repos
	#compile zmqpp
	util/minetester/build_zmqpp.sh

zmqpp: $(ZMQPP_LIB_FILE)

minetest:
	util/minetester/build_minetest.sh

package: deps repos

