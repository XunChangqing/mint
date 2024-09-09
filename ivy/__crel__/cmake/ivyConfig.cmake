set(device_tree "virt.dts" CACHE PATH "path to device tree source")
set(ivy_cfg "ivy_cfg.json" CACHE PATH "path to ivy config json file")

# 添加一个可执行的裸机激励
function(add_ivy_executable exec_name)
  add_executable(${exec_name})
  target_sources(${exec_name} PRIVATE ivy_cfg.h)
  target_sources(${exec_name} PRIVATE ivy_dt.h)
  target_sources(${exec_name} PRIVATE ivy_dt.c)
  target_sources(${exec_name} PRIVATE ivy_pt.S)
  target_sources(${exec_name} PRIVATE ivy_mem_files.h)

  target_sources(${exec_name} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../src/head.S)
  target_sources(${exec_name} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../src/xmain.c)
  target_sources(${exec_name} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../src/spinlock.S)
  target_sources(${exec_name} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../src/pl011.c)
  target_sources(${exec_name} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../src/dw16550.c)
  target_sources(${exec_name} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../src/dummy_uart.c)
  target_sources(${exec_name} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../src/of_fdt.c)
  target_sources(${exec_name} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../src/psci.c)
  target_sources(${exec_name} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../src/smccc_call.S)
  target_sources(${exec_name} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../src/xrt.c)
  target_sources(${exec_name} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../src/print.c)

  target_sources(${exec_name} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../src/libc/string.c)
  target_sources(${exec_name} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../src/libfdt/fdt_addresses.c)
  target_sources(${exec_name} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../src/libfdt/fdt_empty_tree.c)
  target_sources(${exec_name} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../src/libfdt/fdt_ro.c)
  target_sources(${exec_name} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../src/libfdt/fdt_rw.c)
  target_sources(${exec_name} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../src/libfdt/fdt_strerror.c)
  target_sources(${exec_name} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../src/libfdt/fdt_sw.c)
  target_sources(${exec_name} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../src/libfdt/fdt_wip.c)
  target_sources(${exec_name} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../src/libfdt/fdt.c)

  target_include_directories(${exec_name} PRIVATE ${CMAKE_BINARY_DIR})
  target_include_directories(${exec_name} PRIVATE ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../include)
  target_compile_definitions(${exec_name} PRIVATE $<$<COMPILE_LANGUAGE:ASM>: -D__ASSEMBLY__>)
  target_compile_options(${exec_name} PRIVATE -std=gnu99 -fno-builtin -ffreestanding)
  target_link_options(${exec_name} PRIVATE "LINKER:-Tivy.lds,--no-gc-sections,-Bstatic")
  target_link_options(${exec_name} PRIVATE -nostdlib)

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
    COMMAND ${CMAKE_C_COMPILER} -I${CMAKE_BINARY_DIR} -D__LINKAGE__ -E -P -o ivy.lds ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../src/ivy.lds.S
    DEPENDS ivy_app_gen
    VERBATIM
  )
  add_custom_target(linker_script DEPENDS ivy.lds)

  # 预处理生成 memory files 头文件
  # memory files 列表存储于 target 属性内
  set_property(TARGET ${exec_name} PROPERTY MEM_FILES)
  add_custom_command(
    OUTPUT ivy_mem_files.h
    COMMAND ivy_memfile_gen "$<LIST:TRANSFORM,$<TARGET_PROPERTY:${exec_name},MEM_FILES>,PREPEND,-F>"
    DEPENDS $<TARGET_PROPERTY:${exec_name},MEM_FILES>
    COMMAND_EXPAND_LISTS
    VERBATIM
  )

  # executable 目标依赖于 链接器脚本,和设备树解析生成文件
  add_dependencies(${exec_name} linker_script ivy_app_gen)

  # 附加 image 文件生成
  # 合并所有 memory files 文件内容
  add_custom_command(
    TARGET ${exec_name}
    POST_BUILD
    COMMAND PYTHONPATH=${CMAKE_BINARY_DIR} ivy_image_gen --name ${exec_name} --objcopy ${CMAKE_OBJCOPY} "$<LIST:TRANSFORM,$<TARGET_PROPERTY:${exec_name},MEM_FILES>,PREPEND,-F>"
    COMMAND_EXPAND_LISTS
    VERBATIM
  )
endfunction()

function(ivy_target_mem_files target mf)
  set_property(TARGET ${target} APPEND PROPERTY MEM_FILES ${mf})
endfunction(ivy_target_mem_files)


set(mango_seed 0 CACHE STRING "mango random seed")
# 使用 mango 生成裸机激励
function(mango_ivy_target target_name)
  # BUILTIN_EXECUTORS
  # 模型内有 executor component，不向 mango 工具提供 --num_executors 参数
  set(options BUILTIN_EXECUTORS)
  set(oneValueArgs ROOT_COMP ENTRY_ACT)
  set(multiValueArgs INPUTS DEPENDS)

  cmake_parse_arguments(MANGO_TARGET "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN} )

  if(NOT MANGO_TARGET_INPUTS)
    message(FATAL_ERROR, "input of mango_target is empty")
  endif()

  # if(MANGO_TARGET_NUM_EXECUTORS)
  # set(num_executors ${MANGO_TARGET_NUM_EXECUTORS})
  # else()
  #   # 不指定时根据处理核数量确定
  #   set(num_executors 0)
  # endif()

  if(MANGO_TARGET_ROOT_COMP)
    set(root_comp ${MANGO_TARGET_ROOT_COMP})
  else()
    set(root_comp Top)
  endif()

  if(MANGO_TARGET_ENTRY_ACT)
    set(entry_act ${MANGO_TARGET_ENTRY_ACT})
  else()
    set(entry_act Top::Entry)
  endif()

  if(MANGO_TARGET_BUILTIN_EXECUTORS)
    set(arg_executors "--builtin_executors")
  else()
    set(arg_executors "")
  endif()

  # if(MANGO_TARGET_SEED)
  #   set(seed ${MANGO_TARGET_SEED})
  # else()
  #   set(seed 0)
  # endif()

  add_custom_command(
    OUTPUT ${target_name}
    COMMAND PYTHONPATH=${CMAKE_BINARY_DIR} python ${CMAKE_CURRENT_FUNCTION_LIST_DIR}/../tools/run_mango.py --seed ${mango_seed} --root ${root_comp} --entry ${entry_act} ${arg_executors} --soc_output ${target_name} ${MANGO_TARGET_INPUTS}
    DEPENDS ${MANGO_TARGET_INPUTS} ivy_app_gen ${MANGO_TARGET_DEPENDS}
    VERBATIM
    COMMAND_EXPAND_LISTS
    )
  # add_custom_target(
  #   ${target_name}
  #   DEPENDS ${target_name}.c
  # )
endfunction()

# set(ivy_py_lib_path ${CMAKE_CURRENT_LIST_DIR}/../pyivy/ CACHE PATH "path to ivy python library" FORCE)
