#pragma once
#include <ivy/xrt.h>
#include <ivy/print.h>
#include <linux/compiler.h>
#include <stdint.h>

static inline void swo_check(uint64_t* addr_c, uint64_t* addr_d) {
  uint64_t c_v = READ_ONCE(*addr_c);
  uint64_t d_v = READ_ONCE(*addr_d);
  if (c_v == 0 && d_v == 0) {
    printf("simple weakly ordering problem, not permissible\n");
    xrt_exit(1);
  }
}