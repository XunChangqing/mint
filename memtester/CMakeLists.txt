cmake_minimum_required(VERSION 3.27)

project(
  memtester
  VERSION 0.1.0
  DESCRIPTION "memtester based on ivy kit"
  LANGUAGES C ASM
)

find_package(ivy)

add_ivy_executable(memtester)
target_sources(memtester PRIVATE main.c memtester.h sizes.h tests.c tests.h types.h)

# add_custom_command(
#   OUTPUT pattern.h
#   COMMAND PYTHONPATH=${CMAKE_BINARY_DIR} python ${CMAKE_CURRENT_SOURCE_DIR}/pattern.py
# )
