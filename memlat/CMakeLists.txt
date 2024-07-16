cmake_minimum_required(VERSION 3.27)

project(
  qspinlock
  VERSION 0.1.0
  DESCRIPTION "memlat test based on ivy kit"
  LANGUAGES C ASM
)

set(ivy_DIR "${CMAKE_SOURCE_DIR}/../ivy/cmake" CACHE PATH "ivy dir")
# set(device_tree "/home/xuncq/stiwork/ivy_tmp_work/soc/virt_c2.dts")
find_package(ivy)

set(memlat_len "8MiB" CACHE STRING "test length")
set(memlat_line "64KiB" CACHE STRING "cache line")

add_ivy_executable(memlat)
target_sources(memlat PRIVATE main.c)

add_custom_command(
  OUTPUT data.bin memlat_cfg.h
  COMMAND PYTHONPATH=${CMAKE_BINARY_DIR} python ${CMAKE_CURRENT_SOURCE_DIR}/data_gen.py --length ${memlat_len} --line ${memlat_line}
)

target_sources(memlat PRIVATE memlat_cfg.h)
ivy_target_mem_files(memlat data.bin)
