// author : zuoqian
// Copyright 2024. All rights reserved.
#pragma once

#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>

#include "asm.h"
#include "types.h"

// 任意一个核调用都要求所有核结束
void xrt_exit(uint64_t halt_code);

// 或者任意时候出错都输出FAILED到串口，由外部工具负责停止仿真

void xrt_putchar(char c);

// 通过tpidr_el1可以高效得到cpu id
// 在linux内核中，tpidr_el1中保存的是percpu变量的offset，core id也是一个
// percpu变量，通过offset从数组中读取
static __always_inline uint64_t xrt_get_core_id(void) {
  uint64_t off;
  // asm volatile("mrs %x0, tpidr_el1" : "=r"(off) :);
  // 可以不需要volatile，因为只要不破坏输出，可以重复使用
  asm("mrs %x0, tpidr_el1" : "=r"(off) :);
  return off;
}

static __always_inline uint64_t xrt_get_timer() {
  uint64_t cnt;
  // TOFIX，如果EL2存在，必须允许EL1对该寄存器的读取
  MRS(cnt, CNTPCT_EL0);
  return cnt;
}
