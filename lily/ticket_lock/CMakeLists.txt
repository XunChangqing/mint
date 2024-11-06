cmake_minimum_required(VERSION 3.27)

project(
  ticket_lock
  VERSION 0.1.0
  DESCRIPTION "ticket lock test based on ivy kit"
  LANGUAGES C ASM
)

find_package(ivy)

add_ivy_executable(ticket_lock)
target_sources(ticket_lock PRIVATE ticket_lock.c rand_proc.S cfunc.h)

include_directories(${CMAKE_CURRENT_SOURCE_DIR})

if(DEFINED CACHE{use_nvme} OR DEFINED CACHE{use_zni})
  target_sources(ticket_lock PRIVATE pci_main.c)
  if(DEFINED CACHE{use_nvme})
    target_compile_definitions(ticket_lock PRIVATE USE_NVME)
   else()
    target_compile_definitions(ticket_lock PRIVATE USE_ZNI)
  endif()
  set(pci_arg "--pci")
else()
  target_sources(ticket_lock PRIVATE main.c)
  set(pci_arg "")
endif()

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
  target_sources(mp PRIVATE ../c_stressapp/adler32.h ../c_stressapp/adler32.c ../c_stressapp/fill.c pattern.h ../c_stressapp/worker.h ../c_stressapp/worker.c)
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
  OUTPUT ticket_lock.c rand_proc.S
  COMMAND PYTHONPATH=${ivy_binary_dir} python ${CMAKE_CURRENT_SOURCE_DIR}/ticket_lock_main.py --soc_output ticket_lock.c --soc_cooperative ${purslane_debug} ${seed_arg} ${stress_arg} ${pci_arg}
  DEPENDS ticket_lock_main.py ticket_lock_v4.py
)
