cmake_minimum_required(VERSION 3.27)

project(
  mlmo
  VERSION 0.1.0
  DESCRIPTION "mlmo based on ivy kit"
  LANGUAGES C ASM
)

find_package(ivy)

add_ivy_executable(mlmo)
target_sources(mlmo PRIVATE main.c mlmo.c mlmo_t0.c mlmo_t1.c mlmo_t2.c mlmo_t3.c)

# set(CLASS S CACHE STRING "problem size s,w,a(S,W,A)")

# include_directories(${CMAKE_CURRENT_SOURCE_DIR})

# add_custom_command(
#   OUTPUT pattern.h
#   COMMAND PYTHONPATH=${CMAKE_BINARY_DIR} python ${CMAKE_CURRENT_SOURCE_DIR}/pattern_gen.py
# )

# seed random seed
set(seed_arg "")
if(DEFINED CACHE{seed})
  message(STATUS seed exist ${seed})
  set(seed_arg -S ${seed})
endif()

# if(CMAKE_BUILD_TYPE MATCHES "Debug")
#   set(purslane_debug "--debug")
# else()
#   set(purslane_debug)
# endif()

get_target_property(ivy_binary_dir ivy BINARY_DIR)

add_custom_command(
  OUTPUT mlmo.c mlmo_t0.c mlmo_t1.c mlmo_t2.c mlmo_t3.c
  COMMAND PYTHONPATH=${ivy_binary_dir} python ${CMAKE_CURRENT_SOURCE_DIR}/mlmo.py ${seed_arg}
  DEPENDS mlmo.py
)

# target_compile_options(mlmo PUBLIC -E)
