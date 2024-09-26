// author : zuoqian
// Copyright 2024. All rights reserved.

#include "adler32.h"
#include "asm.h"
#include "halt_code.h"
#include "ivy_cfg.h"
#include "ivy_dt.h"
#include "print.h"
#include "worker.h"
#include "xrt.h"

void mango_core_main_func(uint64_t core_id);

void xmain() { mango_core_main_func(xrt_get_core_id()); }
