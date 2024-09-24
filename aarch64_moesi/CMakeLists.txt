cmake_minimum_required(VERSION 3.27)

project(
  aarch64_moesi
  VERSION 0.1.0
  DESCRIPTION "aarch64_moesi based on purslane and ivy kits"
  LANGUAGES C ASM
)

find_package(ivy)

set(num_executors "2" CACHE STRING "number of executors")
set(repeat_times "4" CACHE STRING "repeat times")

add_ivy_executable(aarch64_moesi)
target_sources(aarch64_moesi PRIVATE main.c aarch64_moesi.c)

if(CMAKE_BUILD_TYPE MATCHES "Debug")
  set(purslane_debug "--debug")
else()
  set(purslane_debug)
endif()

add_custom_command(
  OUTPUT aarch64_moesi.c
  COMMAND PYTHONPATH=${CMAKE_BINARY_DIR} python ${CMAKE_CURRENT_SOURCE_DIR}/aarch64_moesi.py --num_repeat_times ${repeat_times} --soc_output aarch64_moesi.c --soc_cooperative ${purslane_debug}
  DEPENDS aarch64_moesi.py
)
