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

void rand_proc();

void rand_inst_sample_main() {
  printf("rand inst sample start\n");
  rand_proc();
  printf("over\n");
}

void xmain() {
  int this_cpu = xrt_get_core_id();
  if (this_cpu == 0) {
    rand_inst_sample_main();
  }
}
