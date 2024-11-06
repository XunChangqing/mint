#pragma once

#include <ivy/print.h>
#include <ivy/xrt.h>
#include <linux/compiler.h>

void check(uint64_t *counter, uint64_t exp) {
  uint64_t dut = READ_ONCE(*counter);
  if (dut != exp) {
    printf("failed, exp %ld dut %ld, counter address: 0x%lx\n", dut, exp,
           (uint64_t)counter);
    xrt_exit(1);
  }
}