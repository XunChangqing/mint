// Copyright 2024 zuoqian, zuoqian@qq.com

#pragma once

#include <asm/sysreg.h>
#include <linux/types.h>

// 任意一个核调用都要求所有核结束
void xrt_exit(unsigned long halt_code);

// 或者任意时候出错都输出FAILED到串口，由外部工具负责停止仿真

void xrt_putchar(char c);

// 通过tpidr_el1可以高效得到cpu id
// 在linux内核中，tpidr_el1中保存的是percpu变量的offset，core id也是一个
// percpu变量，通过offset从数组中读取
static __always_inline unsigned long xrt_get_core_id(void) {
  unsigned long off;
  // asm volatile("mrs %x0, tpidr_el1" : "=r"(off) :);
  // 可以不需要volatile，因为只要不破坏输出，可以重复使用
  asm("mrs %x0, tpidr_el1" : "=r"(off) :);
  return off;
}

static __always_inline unsigned long xrt_timer_get_clk() {
  return read_sysreg(CNTPCT_EL0);
}

static __always_inline double xrt_timer_get_sec() {
  uint64_t cnt = read_sysreg(CNTPCT_EL0);
  uint64_t freq = read_sysreg(CNTFRQ_EL0);
  freq = freq / (1000 * 1000);
  double us = (double)cnt / (double)(freq);
  return us * (1000 * 1000.);
}

static __always_inline unsigned long xrt_timer_get_ms() {
  uint64_t freq = read_sysreg(CNTFRQ_EL0);
  freq = freq / 1000;
  return read_sysreg(CNTPCT_EL0) / freq;
}

static __always_inline unsigned long xrt_timer_get_us() {
  uint64_t freq = read_sysreg(CNTFRQ_EL0);
  freq = freq / (1000 * 1000);
  return read_sysreg(CNTPCT_EL0) / freq;
}
