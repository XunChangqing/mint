mkdir -p build
cd build
cmake --toolchain ../../toolchains/aarch64-generic-gnu.cmake -Divy_DIR=/home/xuncq/stiwork/ivy/cmake -Ddevice_tree=/home/xuncq/stiwork/ivy_tmp_work/soc/virt_c2.dts ..
