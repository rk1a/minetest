.PHONY: all deps repos sdl2 package
SDL2_CMAKE_FILE := lib/SDL/build/lib/cmake/SDL2/sdl2-config.cmake

all: package

deps:
	# Install dependencies
	util/minetester/install_deps.sh

repos:
	# Init all submodules
	git submodule update --init --recursive

$(SDL2_CMAKE_FILE):
	# compile sdl2
	util/minetester/build_sdl2.sh


sdl2: $(SDL2_CMAKE_FILE)

package: deps repos

