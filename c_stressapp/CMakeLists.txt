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

include_directories(${CMAKE_CURRENT_SOURCE_DIR})

add_custom_command(
  OUTPUT pattern.h
  COMMAND PYTHONPATH=${CMAKE_BINARY_DIR} python ${CMAKE_CURRENT_SOURCE_DIR}/pattern_gen.py
)

if(CMAKE_BUILD_TYPE MATCHES "Debug")
  set(purslane_debug "--debug")
else()
  set(purslane_debug)
endif()

add_custom_command(
  OUTPUT c_stressapp.c
  COMMAND PYTHONPATH=${CMAKE_BINARY_DIR} python ${CMAKE_CURRENT_SOURCE_DIR}/c_stressapp.py --soc_output c_stressapp.c --soc_cooperative ${purslane_debug}
  DEPENDS c_stressapp.py
)

set(CMAKE_C_FLAGS "-march=armv8.2-a")
