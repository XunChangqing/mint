// author : zuoqian
// Copyright 2024. All rights reserved.

#include <stddef.h>

#include "asm.h"
#include "halt_code.h"
#include "ivy_cfg.h"
#include "ivy_dt.h"
#include "print.h"
#include "sizes.h"
#include "tests.h"
#include "types.h"
#include "xrt.h"

// 每个 numa 域只使用一个处理核进行测试
#define ONE_CORE_PER_NUMA
// 处理核只测试相同 numa 域的存储
#define LOCAL_MEM_ONLY

// 所有cpu依次进行memory test
int cur_cpu = 0;

bool cpu_done[IVY_DT_NR_CPUS] = {false};

void memory_test() {
  printf("memory test on cpu: %d\n", cur_cpu);
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

  cpu_done[cur_cpu] = true;

  cur_cpu_numa_id = ivy_dt_cpus[cur_cpu].numa_id;

#ifdef ONE_CORE_PER_NUMA
  for (int ci = 0; ci < IVY_DT_NR_CPUS; ci++) {
    if (ci != cur_cpu && cpu_done[ci] &&
        cur_cpu_numa_id == ivy_dt_cpus[ci].numa_id) {
      printf("skip memory test on cpu: %d due to: %d in the same numa\n",
             cur_cpu, ci);
      return;
    }
  }
#endif

  pagesize = IVY_CFG_PAGE_SIZE;
  pagesizemask = (ptrdiff_t) ~(pagesize - 1);

  // 所有可用存储段大跨度检查一遍，防止地址高位发生折叠
  for (int mr = 0; mr < IVY_DT_NUM_FREE_MEMORY; mr++) {
    printf("test memory region start: 0x%lx size: 0x%lx\n",
           ivy_dt_free_memories[mr].start, ivy_dt_free_memories[mr].size);

#ifdef LOCAL_MEM_ONLY
    if (cur_cpu_numa_id != ivy_dt_free_memories[mr].numa_id) {
      printf("skip memory region in a different numa\n");
      continue;
    }
#endif

    buf = (ulv *)ivy_dt_free_memories[mr].start;
    bufsize = ivy_dt_free_memories[mr].size;
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
}

void xmain() {
  int this_cpu = xrt_get_core_id();
  while (cur_cpu != this_cpu) {
    WFE();
  }
  DSB();

  memory_test();

  DSB();
  cur_cpu++;
  // 在发出SEV之前必须 DSB，确保被唤醒的核能够看到 cur_cpu 的新值
  DSB();
  SEV();
}
