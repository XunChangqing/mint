// 测试存储延迟
#include <ivy/print.h>
#include <ivy/xrt.h>
#include <stdint.h>

#include "ivy_cfg.h"
#include "ivy_mem_files.h"
#include "memlat_cfg.h"

#define ONE p = (char **)*p;
#define FIVE ONE ONE ONE ONE ONE
#define TEN FIVE FIVE
#define FIFTY TEN TEN TEN TEN TEN
#define HUNDRED FIFTY FIFTY

static volatile uint64_t use_result_dummy;
void use_pointer(void *result) { use_result_dummy += (long)result; }

extern uint64_t lat_data;

void memlat_test() {
  char **arr = (char **)&lat_data;

  char **head = (char **)arr[HEAD];
  char **p = (char **)arr[HEAD];
  uint64_t *pp = (uint64_t *)(arr);

  uint64_t start_timer_cnt;
  uint64_t end_timer_cnt;
  uint64_t cycles = 0;

  // 遍历一遍
  for (int i = 0; i < WARMUP_TIMES; i++) {
    HUNDRED;
  }

  start_timer_cnt = xrt_timer_get_clk();

  for (int i = 0; i < TEST_TIMES; ++i) {
    HUNDRED;
    // p = (char **)*p;
    // if (p == head) {
    //   cycles++;
    // }
  }

  use_pointer((void *)p);

  end_timer_cnt = xrt_timer_get_clk();

  uint64_t cnt = end_timer_cnt - start_timer_cnt;
  printf("cycles: %lu\n", cnt);
}

void xmain() {
  if (xrt_get_core_id() == 0) {
    memlat_test();
  }
}