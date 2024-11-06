cmake_minimum_required(VERSION 3.27)

project(
  inst_rand_sample
  VERSION 0.1.0
  DESCRIPTION "instruction-level random sample"
  LANGUAGES C ASM
)

find_package(ivy)

add_ivy_executable(inst_rand_sample)
target_sources(inst_rand_sample PRIVATE main.c rand_proc.S)

include_directories(${CMAKE_CURRENT_SOURCE_DIR})

get_target_property(ivy_binary_dir ivy BINARY_DIR)

add_custom_command(
  OUTPUT rand_proc.S
  COMMAND PYTHONPATH=${ivy_binary_dir} python ${CMAKE_CURRENT_SOURCE_DIR}/rand_inst.py
  DEPENDS rand_inst.py
)
