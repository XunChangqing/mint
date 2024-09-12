#include "asm.h"
#include "halt_code.h"
#include "ivy_cfg.h"
#include "ivy_dt.h"
#include "pattern.h"
#include "print.h"
#include "xrt.h"

// 所有cpu依次进行memory test
int cur_cpu = 0;

#define Stride (4 * 1024 * 1024)

void memory_test() {
  printf("memory test on cpu: %d\n", cur_cpu);
  uint64_t times = 0;
  uint64_t pattern_offset = 0;
  uint64_t pattern = 0;
  uint64_t s = 0;

  // 所有可用存储段大跨度检查一遍，防止地址高位发生折叠
  for (int mr = 0; mr < IVY_DT_NUM_FREE_MEMORY; mr++) {
    printf("write memory region start: 0x%lx size: 0x%lx\n",
           ivy_dt_free_memories[mr].start, ivy_dt_free_memories[mr].size);
    for (uint64_t offset = ivy_dt_free_memories[mr].start;
         offset <
         ivy_dt_free_memories[mr].start + ivy_dt_free_memories[mr].size;
         offset += Stride) {
      uint64_t *p = (uint64_t *)offset;
      pattern = pattern_arr[pattern_offset];
      pattern_offset += 1;
      *p = pattern;
      times++;
      // printf("pattern written: %lx\n", pattern);
    }
  }

  // s = 0;
  pattern_offset = 0;
  for (int mr = 0; mr < IVY_DT_NUM_FREE_MEMORY; mr++) {
    printf("read and check memory region start: 0x%lx size: 0x%lx\n",
           ivy_dt_free_memories[mr].start, ivy_dt_free_memories[mr].size);
    for (uint64_t offset = ivy_dt_free_memories[mr].start;
         offset <
         ivy_dt_free_memories[mr].start + ivy_dt_free_memories[mr].size;
         offset += Stride) {
      uint64_t *p = (uint64_t *)offset;
      pattern = pattern_arr[pattern_offset];
      pattern_offset += 1;
      if (*p != pattern) {
        printf("large stride memory_test failed on cpu: %d\n", cur_cpu);
        printf("address 0x%lx, value written in 0x%lx, value read out 0x%lx\n",
               offset, pattern, *p);
        xrt_exit(1);
      }
      // s += 0x0001000100010001ul;
      times++;
    }
  }

  // 每个可用存储内使用第一个64KB数据，小范围检查一遍，防止地址在低位发生折叠
  for (int mr = 0; mr < IVY_DT_NUM_FREE_MEMORY; mr++) {
    uint64_t mr_start = ivy_dt_free_memories[mr].start;
    uint64_t mr_end =
        ivy_dt_free_memories[mr].start + ivy_dt_free_memories[mr].size;

    s = 0;
    for (uint64_t offset = mr_start; offset < mr_end && offset < Stride;
         offset += sizeof(uint64_t)) {
      uint64_t *p = (uint64_t *)offset;
      *p = s;
      s += 0x0001000100010001ul;
      times++;
    }

    s = 0;
    for (uint64_t offset = mr_start; offset < mr_end && offset < Stride;
         offset += sizeof(uint64_t)) {
      uint64_t *p = (uint64_t *)offset;
      if (*p != s) {
        printf("in page memory_test failed on cpu: %d\n", cur_cpu);
        printf("address 0x%x, value written in 0x%lx, value read out 0x%lx\n",
               offset, s, *p);
        xrt_exit(1);
      }
      s += 0x0001000100010001ul;
      times++;
    }
  }

  printf("check times %d on cpu: %d\n", times, cur_cpu);
}

static volatile uint64_t use_result_dummy;

void timer_test() {
  printf("timer_test on cpu: %d\n", cur_cpu);
  uint64_t st = xrt_get_timer();
  for (int i = 0; i < 10000; i++) {
    use_result_dummy += i;
  }
  uint64_t et = xrt_get_timer();
  if (et - st <= 0) {
    printf("timer_test failed on cpu: %d\n", cur_cpu);
    xrt_exit(1);
  }
}

void xmain() {
  int this_cpu = xrt_get_core_id();
  while (cur_cpu != this_cpu) {
    WFE();
  }
  DSB();

  printf("10 bringup test on cpu %d\n", this_cpu);

  memory_test();
  timer_test();

  DSB();
  cur_cpu++;
  // 在发出SEV之前必须 DSB，确保被唤醒的核能够看到 cur_cpu 的新值
  DSB();
  SEV();
}
