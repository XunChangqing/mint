cmake_minimum_required(VERSION 3.27)

project(
  bringup
  VERSION 0.1.0
  DESCRIPTION "system bringup test based on ivy kit"
  LANGUAGES C ASM
)

find_package(ivy)

add_ivy_executable(bringup)
target_sources(bringup PRIVATE main.c pattern.h)

add_custom_command(
  OUTPUT pattern.h
  COMMAND PYTHONPATH=${CMAKE_BINARY_DIR} python ${CMAKE_CURRENT_SOURCE_DIR}/pattern.py
)


set(CMAKE_C_FLAGS "-march=armv8.2-a")
