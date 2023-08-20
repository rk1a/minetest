#! /bin/sh
ROOT=$(pwd)

mkdir -p build/debug

cd build/debug


SDL2_DIR=${ROOT}/lib/SDL/build/lib/cmake/SDL2/

echo ${SDL2_DIR}

cmake ../.. -DRUN_IN_PLACE=TRUE -DBUILD_HEADLESS=1 -DSDL2_DIR=$SDL2_DIR -DCMAKE_BUILD_TYPE=RelWithDebInfo
make -j$(( $(nproc) > 1 ? $(nproc) - 1 : 1 ))

cd ../..
mv bin/minetest bin/debug
