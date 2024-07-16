// 测试存储延迟
#include <stdint.h>

#include "ivy_cfg.h"
#include "ivy_mem_files.h"
#include "memlat_cfg.h"
#include "print.h"
#include "xrt.h"

#define ONE p = (char **)*p;
#define FIVE ONE ONE ONE ONE ONE
#define TEN FIVE FIVE
#define FIFTY TEN TEN TEN TEN TEN
#define HUNDRED FIFTY FIFTY

static volatile uint64_t use_result_dummy;
void use_pointer(void *result) { use_result_dummy += (long)result; }

void memlat_test() {
  // TOFIX
  // 存储分配
  // 将文件内容拷贝到分配存储
  // 文件内容为索引号
  char *arr;
  // IVY_MEM_FILE_0_DATA_BIN_START;

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

  start_timer_cnt = xrt_get_timer();

  for (int i = 0; i < TEST_TIMES; ++i) {
    HUNDRED;
    // p = (char **)*p;
    // if (p == head) {
    //   cycles++;
    // }
  }

  use_pointer((void *)p);

  end_timer_cnt = xrt_get_timer();

  uint64_t cnt = end_timer_cnt - start_timer_cnt;
  printf("cycles: %lu\n", cnt);
}

void xmain() {
  if (xrt_get_core_id() == 0) {
    // IVY_MEM_FILE_0_DATA_BIN_START
    memlat_test();
  }
}