// author : zuoqian
// Copyright 2024. All rights reserved.

#include <ivy/halt_code.h>
#include <ivy/print.h>
#include <ivy/sync.h>
#include <ivy/xrt.h>
#include <linux/atomic.h>
#include <linux/types.h>
#include <stdint.h>

#include "ivy_cfg.h"
#include "ivy_dt.h"
#include "sizes.h"
#include "tests.h"
#include "types.h"

// 所有cpu依次进行memory test
atomic_t cur_cpu = ATOMIC_INIT(0);

// typedef unsigned long volatile ulv;
typedef uintptr_t volatile upv;

void memory_test() {
  printf("memory test on cpu: %d\n", atomic_read(&cur_cpu));
  uintptr_t idx = 0;

  for (int mr = 0; mr < IVY_DT_NUM_FREE_MEMORY; mr++) {
    printf("setting memory region start: 0x%lx size: 0x%lx\n",
           ivy_dt_free_memories[mr].start, ivy_dt_free_memories[mr].size);
    uint64_t mr_start = ivy_dt_free_memories[mr].start;
    uint64_t mr_size = ivy_dt_free_memories[mr].size;
    upv *buf = (upv *)(mr_start);

    for (size_t mr_j = 0; mr_j < mr_size / sizeof(uintptr_t); mr_j++) {
      *buf = ((idx) % 2) == 0 ? (uintptr_t)buf : ~((uintptr_t)buf);
      idx++;
      buf++;
    }
  }

  idx = 0;

  for (int mr = 0; mr < IVY_DT_NUM_FREE_MEMORY; mr++) {
    printf("testing memory region start: 0x%lx size: 0x%lx\n",
           ivy_dt_free_memories[mr].start, ivy_dt_free_memories[mr].size);
    uint64_t mr_start = ivy_dt_free_memories[mr].start;
    uint64_t mr_size = ivy_dt_free_memories[mr].size;
    upv *buf = (upv *)(mr_start);

    for (size_t mr_j = 0; mr_j < mr_size / sizeof(uint64_t); mr_j++) {
      uintptr_t exp_val = ((idx) % 2) == 0 ? (uintptr_t)buf : ~((uintptr_t)buf);
      if (*buf != exp_val) {
        printf("FAILURE: dut val 0x%08x exp val 0x%08x, address 0x%08x\n", *buf,
               exp_val, (uintptr_t)buf);
        xrt_exit(1);
      }

      idx++;
      buf++;
    }
  }
}

bool cpu_do_local_memtest[IVY_DT_NR_CPUS] = {false};

void choose_local_cpu() {
  for (int i = 0; i < IVY_DT_NR_CPUS; i++) {
    uint64_t cur_numa_id = ivy_dt_cpus[i].numa_id;
    bool first_in_numa = true;
    for (int j = 0; j < i; j++) {
      uint64_t numa_id = ivy_dt_cpus[j].numa_id;
      if (cur_numa_id == numa_id) {
        first_in_numa = false;
        break;
      }
    }
    if (first_in_numa) {
      cpu_do_local_memtest[i] = true;
    }
  }
}

void test_range(uint64_t start, uint64_t size) {
  uint64_t times = 0;
  uint64_t pattern_offset = 0;
  uint64_t pattern = 0;
  uint64_t s = 0;
  uint64_t cur_cpu_numa_id;
  ptrdiff_t pagesizemask;
  void volatile *buf, *aligned;
  ulv *bufa, *bufb;
  size_t pagesize, wantraw, wantmb, wantbytes, wantbytes_orig, bufsize, halflen,
      count;

  cur_cpu_numa_id = ivy_dt_cpus[atomic_read(&cur_cpu)].numa_id;

  pagesize = IVY_CFG_PAGE_SIZE;
  pagesizemask = (ptrdiff_t) ~(pagesize - 1);

  buf = (ulv *)start;
  bufsize = size;
  // Do alighnment here as well, as some cases won't trigger above if you
  // define out the use of mlock() (cough HP/UX 10 cough).
  if ((size_t)buf % pagesize) {
    /* printf("aligning to page -- was 0x%tx\n", buf); */
    aligned = (void volatile *)((size_t)buf & pagesizemask) + pagesize;
    /* printf("  now 0x%tx -- lost %d bytes\n", aligned,
     *      (size_t) aligned - (size_t) buf);
     */
    bufsize -= ((size_t)aligned - (size_t)buf);
  } else {
    aligned = buf;
  }

  halflen = bufsize / 2;
  count = halflen / sizeof(ul);
  bufa = (ulv *)aligned;
  bufb = (ulv *)((size_t)aligned + halflen);

  test_stuck_address(aligned, bufsize / sizeof(ul));
}

void para_local_memtest() {
  uint64_t this_cpu = xrt_get_core_id();
  uint64_t numa_id = ivy_dt_cpus[this_cpu].numa_id;

  if (!cpu_do_local_memtest[this_cpu]) {
    printf("skip cpu %d on parallel local memtest\n", this_cpu);
    return;
  }

  printf("local memtest on cpu %d\n", this_cpu);

  for (int mr = 0; mr < IVY_DT_NUM_FREE_MEMORY; mr++) {
    uint64_t fm_start = ivy_dt_free_memories[mr].start;
    uint64_t fm_size = ivy_dt_free_memories[mr].size;
    uint64_t fm_numa_id = ivy_dt_free_memories[mr].numa_id;

    if (fm_numa_id != numa_id) {
      printf("skip memory region 0x%lx 0x%lx on cpu %d\n", fm_start, fm_size,
             this_cpu);
    } else {
      printf("test memory region 0x%lx 0x%lx on cpu %d\n", fm_start, fm_size,
             this_cpu);

      test_range(fm_start, fm_size);
    }
  }
}

void xmain() {
  int this_cpu = xrt_get_core_id();
  if (this_cpu == 0) {
    choose_local_cpu();
  }

  while (atomic_read_acquire(&cur_cpu) != this_cpu) {
    wfe();
  }

  // 所有处理核依次测试所有存储
  memory_test();

  atomic_fetch_add_release(1, &cur_cpu);
  // 在发出SEV之前必须 DSB，确保被唤醒的核能够看到 cur_cpu 的新值
  sev();

  cpu_barrier_wait();

  // 每个 numa 一个处理核大压力测试本 numa 内存储，使用 memtester 内方法
  para_local_memtest();
}
