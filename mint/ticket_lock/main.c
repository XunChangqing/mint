// author : zuoqian
// Copyright 2024. All rights reserved.

#include <ivy/halt_code.h>
#include <ivy/print.h>
#include <ivy/sync.h>
#include <ivy/xrt.h>
#include <ivy/pci.h>

#include "ivy_cfg.h"
#include "ivy_dt.h"

void mango_core_main_func(uint64_t core_id);

void xmain() {
  mango_core_main_func(xrt_get_core_id());
}
