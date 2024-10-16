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

# seed random seed
set(seed_arg "")
if(DEFINED CACHE{seed})
  message(STATUS seed exist ${seed})
  set(seed_arg -S ${seed})
endif()

if(CMAKE_BUILD_TYPE MATCHES "Debug")
  set(purslane_debug "--debug")
else()
  set(purslane_debug)
endif()

get_target_property(ivy_binary_dir ivy BINARY_DIR)

add_custom_command(
  OUTPUT aarch64_moesi.c
  COMMAND PYTHONPATH=${ivy_binary_dir} python ${CMAKE_CURRENT_SOURCE_DIR}/aarch64_moesi.py --num_repeat_times ${repeat_times} --soc_output aarch64_moesi.c --soc_cooperative ${purslane_debug} ${seed_arg}
  DEPENDS aarch64_moesi.py
)
