add_custom_command(
    OUTPUT sysreg-defs.h
    COMMAND awk -f ${CMAKE_CURRENT_LIST_DIR}/gen-sysreg.awk ${CMAKE_CURRENT_LIST_DIR}/sysreg > sysreg-defs.h
)

add_custom_command(
    OUTPUT cpucaps.h
    COMMAND awk -f ${CMAKE_CURRENT_LIST_DIR}/gen-cpucaps.awk ${CMAKE_CURRENT_LIST_DIR}/cpucaps > cpucaps.h
)

add_custom_target(sysreg-defs DEPENDS sysreg-defs.h)
add_custom_target(cpucaps-defs DEPENDS cpucaps.h)

add_dependencies(ivy sysreg-defs cpucaps-defs)

target_include_directories(ivy PUBLIC ${CMAKE_CURRENT_BINARY_DIR})
