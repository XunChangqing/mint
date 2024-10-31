#pragma once

#include <ivy/print.h>
#include <ivy/xrt.h>
#include <stdint.h>

static inline void tl_check(uint64_t *counter, uint64_t exp_val) {
  if (READ_ONCE(*counter) != exp_val) {
    printf("counter dut %lu exp %lu\n", READ_ONCE(*counter), exp_val);
    xrt_exit(1);
  }
}