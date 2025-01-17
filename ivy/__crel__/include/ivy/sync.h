//  Copyright (C) 2023-2024 zuoqian
//  Licensed under the terms of the GNU General Public License version 2 (only).
//  See the file COPYING for details.

#pragma once

#ifdef __ASSEMBLY__
#error(can only be included in assembly files)
#endif

#include <linux/types.h>

// 物理 cpu barrier 同步等待
void cpu_barrier_wait();
