// author : zuoqian
// Copyright 2024. All rights reserved.

#include <ivy/halt_code.h>
#include <ivy/print.h>
#include <ivy/xrt.h>
#include <linux/atomic.h>
#include <linux/compiler.h>
#include <stdint.h>

#include "ivy_cfg.h"
#include "ivy_dt.h"
#include "user_map.h"

void xmain() {
  int this_cpu = xrt_get_core_id();
  if (this_cpu == 0) {
    printf("test user mapped memory\n");

    uint64_t *p = (uint64_t *)(USER_ADDR);
    WRITE_ONCE(*p, 2);
    uint64_t v = READ_ONCE(*p);
    printf("value %lx\n", v);

    printf("hello world\n");
  }
}
