cmake_minimum_required(VERSION 3.27)

project(
  mp
  VERSION 0.1.0
  DESCRIPTION "barrier litmus test based on ivy kit"
  LANGUAGES C ASM
)

find_package(ivy)

add_ivy_executable(mp)
target_sources(mp PRIVATE main.c mp.c rand_proc.S)

include_directories(${CMAKE_CURRENT_SOURCE_DIR})

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
  OUTPUT mp.c rand_proc.S
  COMMAND PYTHONPATH=${ivy_binary_dir} python ${CMAKE_CURRENT_SOURCE_DIR}/mp_main.py --soc_output mp.c --soc_cooperative ${purslane_debug} ${seed_arg}
  DEPENDS mp_main.py mp_v2.py mp_v3.py mp_v4.py
)
