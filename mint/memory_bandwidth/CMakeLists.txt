cmake_minimum_required(VERSION 3.27)

project(
  bringup
  VERSION 0.1.0
  DESCRIPTION "system membw test based on ivy kit"
  LANGUAGES C ASM
)

find_package(ivy)

add_ivy_executable(membw)
target_sources(membw PRIVATE main.c mb.h)

get_target_property(ivy_binary_dir ivy BINARY_DIR)

add_custom_command(
  OUTPUT mb.h
  COMMAND PYTHONPATH=${ivy_binary_dir} python ${CMAKE_CURRENT_SOURCE_DIR}/mb.py
  DEPENDS mb.py test_cfg.py
)
