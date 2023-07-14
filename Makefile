.PHONY: all deps repos sdl2 package zmqpp minetester minetest install demo proto clean

MINETESTER_VERSION := 0.0.1
SDL2_CMAKE_FILE := lib/SDL/build/lib/cmake/SDL2/sdl2-config.cmake
ZMQPP_LIB_FILE := lib/zmqpp/build/max-g++/libzmqpp.a
MINETEST_BINARY := bin/minetest
MINETESTER_WHEEL := build/package/wheel/minetester-$(MINETESTER_VERSION)-py3-none-manylinux_2_35_x86_64.whl

default: minetest 

deb_deps:
	# Install debian dependencies
	util/minetester/install_deps.sh

python_build_deps:
	pip install -r build_requirements.txt

repos:
	# Init all submodules
	git submodule update --init --recursive

$(SDL2_CMAKE_FILE): repos
	# compile sdl2
	util/minetester/build_sdl2.sh

sdl2: $(SDL2_CMAKE_FILE)

proto:
	util/minetester/compile_proto.sh

$(ZMQPP_LIB_FILE): repos
	#compile zmqpp
	util/minetester/build_zmqpp.sh

zmqpp: $(ZMQPP_LIB_FILE)


$(MINETEST_BINARY): repos sdl2 zmqpp proto
	util/minetester/build_minetest.sh

minetest: $(MINETEST_BINARY)

minetester:
	util/minetester/build_minetester.sh

install:
	pip install $(MINETESTER_WHEEL)

demo:
	python -m minetester.scripts.test_loop

clean:
	util/minetester/clean.sh
