cmake_minimum_required(VERSION 3.27)

project(
  adoc
  VERSION 0.1.0
  DESCRIPTION "address dependency with object construction based on ivy kit"
  LANGUAGES C ASM
)

find_package(ivy)

add_ivy_executable(adoc)
target_sources(adoc PRIVATE main.c adoc.c rand_proc.S)

include_directories(${CMAKE_CURRENT_SOURCE_DIR})

set(seed "" CACHE STRING "random seed")
option(armv7 "user armv7 compatible approaches for ordering")
option(stress "combine with the stressapp")

# seed random seed
set(seed_arg "")
if(seed)
  message(STATUS seed exist ${seed})
  set(seed_arg -S ${seed})
endif()

if(stress)
  message(STATUS stress)
  set(stress_arg "--stress")
  # c_stressapp
  target_sources(adoc PRIVATE ../c_stressapp/adler32.h ../c_stressapp/adler32.c ../c_stressapp/fill.c pattern.h ../c_stressapp/worker.h ../c_stressapp/worker.c)
  include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../c_stressapp)
  
  add_custom_command(
    OUTPUT pattern.h
    COMMAND PYTHONPATH=${CMAKE_BINARY_DIR} python ${CMAKE_CURRENT_SOURCE_DIR}/../c_stressapp/pattern_gen.py
  )
else()
  set(stress_arg "")
endif()

set(armv7_arg "")
if(armv7)
  set(armv7_arg "--armv7")
endif()

if(CMAKE_BUILD_TYPE MATCHES "Debug")
  set(purslane_debug "--debug")
else()
  set(purslane_debug)
endif()

get_target_property(ivy_binary_dir ivy BINARY_DIR)

add_custom_command(
  OUTPUT adoc.c rand_proc.S
  COMMAND PYTHONPATH=${ivy_binary_dir} python ${CMAKE_CURRENT_SOURCE_DIR}/adoc_main.py --soc_output adoc.c --soc_cooperative ${purslane_debug} ${seed_arg} ${stress_arg} ${armv7_arg}
  DEPENDS adoc_main.py adoc_v4.py
)
