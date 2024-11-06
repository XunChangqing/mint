// Copyright 2024 zuoqian, zuoqian@qq.com

#include <ivy/halt_code.h>
#include <ivy/print.h>
#include <ivy/xrt.h>

#include "adler32.h"
#include "ivy_cfg.h"
#include "ivy_dt.h"
#include "worker.h"

void mango_core_main_func(uint64_t core_id);

void xmain() { mango_core_main_func(xrt_get_core_id()); }
