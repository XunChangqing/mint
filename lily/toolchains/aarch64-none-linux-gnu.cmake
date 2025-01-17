set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR aarch64)

set(CMAKE_C_COMPILER "aarch64-none-linux-gnu-gcc")
set(CMAKE_CXX_COMPILER "aarch64-none-linux-gnu-g++")
set(CMAKE_OBJCOPY "aarch64-none-linux-gnu-objcopy")

if(NOT CMAKE_FIND_ROOT_PATH_MODE_PROGRAM)
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
endif()
if(NOT CMAKE_FIND_ROOT_PATH_MODE_LIBRARY)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
endif()
if(NOT CMAKE_FIND_ROOT_PATH_MODE_INCLUDE)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
endif()
if(NOT CMAKE_FIND_ROOT_PATH_MODE_PACKAGE)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)
endif()

# cache flags
# set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS}" CACHE STRING "c flags")
# set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}" CACHE STRING "c++ flags")

set(CMAKE_C_FLAGS "-march=armv8.2-a" CACHE STRING "c flags")
set(CMAKE_ASM_FLAGS "-march=armv8.2-a" CACHE STRING "asm flags")