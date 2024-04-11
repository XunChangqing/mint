cmake_minimum_required(VERSION 3.27)

project(
  bringup
  VERSION 0.1.0
  DESCRIPTION "system bringup test based on ivy kit"
  LANGUAGES C ASM
)

# set(ivy_DIR "/home/xuncq/stiwork/ivy/cmake")
# set(device_tree "/home/xuncq/stiwork/ivy_tmp_work/soc/virt_c2.dts")
find_package(ivy)

add_ivy_executable(bringup)
target_sources(bringup PRIVATE main.c)
