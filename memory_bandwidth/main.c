// author : zuoqian
// Copyright 2024. All rights reserved.

#include <ivy/halt_code.h>
#include <ivy/print.h>
#include <ivy/sync.h>
#include <ivy/xrt.h>
#include <linux/atomic.h>
#include <linux/types.h>
#include <stdint.h>
#include <string.h>

#include "ivy_cfg.h"
#include "ivy_dt.h"

// 所有cpu依次进行memory test

// uint64_t st = xrt_get_timer();

struct job {
  size_t size;
  void *src;
  void *dst;
  bool cpu_mask;
};

struct chip_job {
  char *name;
  struct job cpu_jobs[IVY_DT_NR_CPUS];
};

// struct chip_job job_list[] = {
//     {.cpu_jobs = {{.size = 4}, {.size = 4}}},
// };

#include "mb.h"

void xmain() {
  int this_cpu = xrt_get_core_id();

  for (int i = 0; i < sizeof(job_list) / sizeof(job_list[0]); i++) {
    if (this_cpu == 0) {
      printf("job %d %s start\n", i, job_list[i].name);
    }

    cpu_barrier_wait();
    uint64_t st = xrt_get_timer();

    struct job *this_cpu_job = &(job_list[i].cpu_jobs[this_cpu]);

    if (this_cpu_job->cpu_mask) {
      memcpy(this_cpu_job->dst, this_cpu_job->src, this_cpu_job->size);
    }

    cpu_barrier_wait();
    uint64_t et = xrt_get_timer();

    if (this_cpu == 0) {
      printf("job %d end, time 0x%lx\n", i, et - st);
    }
  }
}
