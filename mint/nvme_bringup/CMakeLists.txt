cmake_minimum_required(VERSION 3.27)

project(
  nvme_bringup
  VERSION 0.1.0
  DESCRIPTION "nvme_bringup based on ivy kit"
  LANGUAGES C ASM
)

find_package(ivy)

add_ivy_executable(nvme_bringup)
target_sources(nvme_bringup PRIVATE main.c)
# user_pgt.S user_map.h)

include_directories(${CMAKE_CURRENT_SOURCE_DIR})

get_target_property(ivy_binary_dir ivy BINARY_DIR)

# add_custom_command(
#   OUTPUT user_pt.S user_map.h
#   COMMAND PYTHONPATH=${ivy_binary_dir} python ${CMAKE_CURRENT_SOURCE_DIR}/um.py
#   DEPENDS um.py
# )
