cmake_minimum_required(VERSION 3.27)

project(
  cache_coherency
  VERSION 0.1.0
  DESCRIPTION "cache coherency test based on ivy kit"
  LANGUAGES C ASM
)

set(ivy_DIR "${CMAKE_SOURCE_DIR}/../ivy/cmake" CACHE PATH "ivy dir")
message(INFO "${ivy_DIR}")
# set(device_tree "/home/xuncq/stiwork/ivy_tmp_work/soc/virt_c2.dts")
find_package(ivy)

set(mint_DIR "${CMAKE_SOURCE_DIR}/../cmake" CACHE PATH "mint dir")
find_package(mint)

add_ivy_executable(cache_coherency)
target_include_directories(cache_coherency PRIVATE ${CMAKE_SOURCE_DIR} ${CMAKE_BINARY_DIR})
target_sources(cache_coherency PRIVATE main.c cc_mango.c cl_def.h)

add_custom_command(
  OUTPUT cl_def.h
  COMMAND PYTHONPATH=${CMAKE_BINARY_DIR} python ${CMAKE_CURRENT_SOURCE_DIR}/sel_cl.py
)

mango_ivy_target(cc_mango.c BUILTIN_EXECUTORS INPUTS ivy_app_cfg.pss ${CMAKE_SOURCE_DIR}/cc.pss)
