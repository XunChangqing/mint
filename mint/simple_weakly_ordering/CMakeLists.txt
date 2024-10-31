cmake_minimum_required(VERSION 3.27)

project(
  swo
  VERSION 0.1.0
  DESCRIPTION "barrier litmus test based on ivy kit"
  LANGUAGES C ASM
)

find_package(ivy)

add_ivy_executable(swo)
target_sources(swo PRIVATE main.c swo.c rand_proc.S)

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

if(DEFINED CACHE{stress})
  message(STATUS stress)
  set(stress_arg "--stress")
  # c_stressapp
  target_sources(swo PRIVATE ../c_stressapp/adler32.h ../c_stressapp/adler32.c ../c_stressapp/fill.c pattern.h ../c_stressapp/worker.h ../c_stressapp/worker.c)
  include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../c_stressapp)
  
  add_custom_command(
    OUTPUT pattern.h
    COMMAND PYTHONPATH=${CMAKE_BINARY_DIR} python ${CMAKE_CURRENT_SOURCE_DIR}/../c_stressapp/pattern_gen.py
  )
else()
  set(stress_arg "")
endif()

get_target_property(ivy_binary_dir ivy BINARY_DIR)

add_custom_command(
  OUTPUT swo.c rand_proc.S
  COMMAND PYTHONPATH=${ivy_binary_dir} python ${CMAKE_CURRENT_SOURCE_DIR}/swo_main.py --soc_output swo.c --soc_cooperative ${purslane_debug} ${seed_arg} ${stress_arg}
  DEPENDS swo_main.py swo_v2.py swo_v3.py swo_v4.py
)
