//  Copyright (C) 2023-2024 zuoqian
//  Licensed under the terms of the GNU General Public License version 2 (only).
//  See the file COPYING for details.

#include <ivy/sync.h>
#include <ivy_dt.h>
#include <linux/atomic.h>
#include <linux/limits.h>
#include <linux/types.h>

struct CpuBarrier {
  atomic_t in;
  atomic_t out;
};

struct CpuBarrier cpu_barrier = {.in = ATOMIC_INIT(0), .out = ATOMIC_INIT(0)};

#define BARRIER_IN_THRESHOLD (INT_MAX / 2)

// 参考 pthread nptl 中 pthread_barrier_wait
// inspired by the pthread_barrier_wait in the pthread/nptl
void cpu_barrier_wait() {
  //   how many cores entered so far, including ourself
  int i;

reset_restart:
  i = atomic_fetch_add(1, &cpu_barrier.in) + 1;
  sev();

  int count = IVY_DT_NR_CPUS;

  int max_in_before_reset = BARRIER_IN_THRESHOLD - BARRIER_IN_THRESHOLD % count;

  if (i > max_in_before_reset) {
    while (i > max_in_before_reset) {
      wfe();
      i = atomic_read(&cpu_barrier.in);
    }

    goto reset_restart;
  }

  int cr = (((i - 1) / count) + 1) * count;
  while (atomic_read(&cpu_barrier.in) < cr) {
    wfe();
  }

  int o;
ready_to_leave:
  o = atomic_fetch_add(1, &cpu_barrier.out) + 1;

  if (o == max_in_before_reset) {
    smp_rmb();
    atomic_set(&cpu_barrier.out, 0);
    atomic_set_release(&cpu_barrier.in, 0);
    sev();
  }
}
