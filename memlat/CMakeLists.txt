cmake_minimum_required(VERSION 3.27)

project(
  qspinlock
  VERSION 0.1.0
  DESCRIPTION "memlat test based on ivy kit"
  LANGUAGES C ASM
)

find_package(ivy)

set(memlat_len "8MiB" CACHE STRING "test length")
set(memlat_line "64KiB" CACHE STRING "cache line")

add_ivy_executable(memlat)
target_sources(memlat PRIVATE main.c)

get_target_property(ivy_binary_dir ivy BINARY_DIR)

add_custom_command(
  OUTPUT data.S memlat_cfg.h
  COMMAND PYTHONPATH=${ivy_binary_dir} python ${CMAKE_CURRENT_SOURCE_DIR}/data_gen.py --length ${memlat_len} --line ${memlat_line}
  DEPENDS data_gen.py
)

target_sources(memlat PRIVATE memlat_cfg.h data.S)
