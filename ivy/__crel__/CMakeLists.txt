add_library(ivy STATIC)

target_include_directories(ivy SYSTEM PUBLIC include include/uapi arch/arm64/include arch/arm64/include/uapi include/cstd)

target_sources(ivy PRIVATE ivy_cfg.h)
target_sources(ivy PRIVATE ivy_dt.h)
# target_sources(ivy PRIVATE ivy_mem_files.h)
target_sources(ivy PRIVATE ivy_dt.c)
target_sources(ivy PRIVATE ivy_pt.S)
target_include_directories(ivy PUBLIC ${CMAKE_CURRENT_BINARY_DIR})

# 解析 设备树和配置文件，产生 py、pss、c输出
add_custom_command(
  OUTPUT ivy_cfg.h ivy_dt.h ivy_dt.c ivy_pt.S ivy_app_cfg.py
  COMMAND PYTHONPATH=${CMAKE_BINARY_DIR} ivy_app_gen --device_tree ${device_tree} --cfg ${ivy_cfg}
  VERBATIM
)
add_custom_target(ivy_app_gen DEPENDS ivy_cfg.h ivy_dt.h ivy_pt.S)

# 预处理链接器脚本文件
add_custom_command(
  OUTPUT ivy.lds
  COMMAND ${CMAKE_C_COMPILER} -I${CMAKE_CURRENT_BINARY_DIR} -D__LINKAGE__ -E -P -o ivy.lds ${CMAKE_CURRENT_SOURCE_DIR}/src/ivy.lds.S
  DEPENDS ivy_app_gen
  VERBATIM
)
add_custom_target(ivy_linker_script DEPENDS ivy.lds)

# executable 目标依赖于 链接器脚本,和设备树解析生成文件
add_dependencies(ivy ivy_linker_script ivy_app_gen)

# target_compile_definitions(ivy PUBLIC -D__KERNEL__)
target_compile_definitions(ivy PUBLIC $<$<COMPILE_LANGUAGE:ASM>: -D__ASSEMBLY__>)
# -Werror=implicit)
target_compile_definitions(ivy PUBLIC __KERNEL__ __LITTLE_ENDIAN CONFIG_SMP CONFIG_64BIT CONFIG_ARM64 CONFIG_HAVE_ARM_SMCCC CONFIG_ARM64_LSE_ATOMICS CONFIG_FUNCTION_ALIGNMENT=8)
target_compile_options(ivy PUBLIC -fno-strict-overflow -nostdinc -std=gnu99 -fno-builtin -ffreestanding -Wall -falign-functions=8)
target_link_options(ivy PUBLIC "LINKER:-T${CMAKE_CURRENT_BINARY_DIR}/ivy.lds,--no-gc-sections,-Bstatic")
target_link_options(ivy PUBLIC -nostdlib)

add_subdirectory(arch)
add_subdirectory(include)
add_subdirectory(src)