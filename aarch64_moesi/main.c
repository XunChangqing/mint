#include <stdint.h>
#include "xrt.h"

void mango_core_main_func(uint64_t core_id);

void xmain() {
    mango_core_main_func(xrt_get_core_id());
}