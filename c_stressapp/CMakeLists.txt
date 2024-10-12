cmake_minimum_required(VERSION 3.27)

project(
  c_stressapp
  VERSION 0.1.0
  DESCRIPTION "stressapp based on ivy kit"
  LANGUAGES C ASM
)

find_package(ivy)

add_ivy_executable(stressapp)
target_sources(stressapp PRIVATE main.c adler32.h adler32.c fill.c pattern.h worker.h worker.c c_stressapp.c)

set(CLASS S CACHE STRING "problem size s,w,a(S,W,A)")

include_directories(${CMAKE_CURRENT_SOURCE_DIR})

add_custom_command(
  OUTPUT pattern.h
  COMMAND PYTHONPATH=${CMAKE_BINARY_DIR} python ${CMAKE_CURRENT_SOURCE_DIR}/pattern_gen.py
)

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
  OUTPUT c_stressapp.c
  COMMAND PYTHONPATH=${ivy_binary_dir} python ${CMAKE_CURRENT_SOURCE_DIR}/c_stressapp.py --soc_output c_stressapp.c --soc_cooperative ${purslane_debug} --pclass ${CLASS} ${seed_arg}
  DEPENDS c_stressapp.py
)
