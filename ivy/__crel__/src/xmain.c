#include <asm/barrier.h>
#include <ivy/halt_code.h>
#include <ivy/print.h>
#include <ivy/sync.h>
#include <ivy/xrt.h>
#include <linux/psci.h>

#include "dw16550.h"
#include "ivy_cfg.h"
#include "ivy_dt.h"
#include "libfdt/libfdt.h"
#include "of_fdt.h"
#include "pl011.h"

void _halt();
void _error_halt(uint64_t halt_code);
void _secondary_entry();

// head.S 将fdt地址存到该变量
uintptr_t fdt_pointer;

// #define IVT_DT_UART_BARD_RATE (115200)
// #define IVT_DT_UART_BARD_RATE (921600)

// 主核负责环境建立
void env_setup() {
#ifdef IVY_DT_STDOUT_PL011
  pl011_cfg _pl011_cfg;
  _pl011_cfg.baudrate = IVT_DT_UART_BARD_RATE;
  _pl011_cfg.bitcount = 0b11;
  _pl011_cfg.enablefifo = true;
  _pl011_cfg.enablerx = true;
  _pl011_cfg.enabletx = true;
  _pl011_cfg.enableuart = true;
  pl011_init(IVY_DT_STDOUT_PL011_BASE, &_pl011_cfg);
#endif

#ifdef DT_STDOUT_DW16550
  dw16550_init(DT_STDOUT_DW16550_BASE, IVT_DT_UART_BARD_RATE);
#endif
}

// 用户提供
void user_setup() __attribute__((weak));
void user_setup() {}

// 应用入口
extern void xmain();

// void fdt_print_node_tree_name(void* fdt, int offset) {
//   int n;
//   fdt_for_each_subnode(n, fdt, offset) {
//     int len;
//     const char* name = fdt_get_name(fdt, n, &len);
//     if (len < 0) {
//       _error_halt(HALT_CODE_FDT_ERROR);
//     }
//     printf("node name: %s\n", name);

//     fdt_print_node_tree_name(fdt, n);
//   }
// }

// void debug_fdt(void* fdt) {
//   fdt32_t magic = fdt_get_header(fdt, magic);
//   // 必须判断主cpu是哪个
//   fdt32_t boot_cpuid_phys = fdt_get_header(fdt, boot_cpuid_phys);
//   printf("magic: %x, boot cpuid phys: %x\n", magic, boot_cpuid_phys);

//   fdt_print_node_tree_name(fdt, 0);
// }

int cpu_psci_cpu_boot(unsigned int cpu) {
  psci_cpu_on(ivy_dt_cpu_id_map[cpu], (uint64_t)_secondary_entry);
  return 0;
}

#ifdef IVY_CFG_NO_BOOTER
// 从核释放标志
uint64_t release_no_booter = 0;
#endif

void bringup_secondary_cpus() {
#if IVY_DT_NR_CPUS > 1
#ifdef IVY_CFG_NO_BOOTER
  release_no_booter = 1;
#else

// use psci
#ifdef IVY_DT_PSCI_CONDUIT_SMC
  cpu_psci_init(PSCI_CONDUIT_SMC);
#elif defined DT_PSCI_CONDUIT_HVC
  cpu_psci_init(PSCI_CONDUIT_HVC);
#else
#error psci conduit must be set
#endif

  // 通过psci唤醒所有除自己以外的从核
  int this_cpu = xrt_get_core_id();
  for (int cpu = 0; cpu < IVY_DT_NR_CPUS; cpu++) {
    if (this_cpu != cpu) {
      cpu_psci_cpu_boot(cpu);
    }
  }

#endif

#endif
}

void primary_main() {
  int ec = 0;
  printf("check fdt\n");
  // 主核负责检查运行时传入的fdt是否与预先提供的一致
  ec = fdt_check((void*)fdt_pointer);
  if (ec) {
    _error_halt(HALT_CODE_FDT_ERROR);
  }

  env_setup();
  user_setup();

  printf("Copyright (C) 2024 ivy\n");
  // 一定时间内不输出START，表示出错了
  printf("$START$\n");

  // 唤醒除自己以外的从核
  bringup_secondary_cpus();

  cpu_barrier_wait();
  xmain();
  cpu_barrier_wait();
  // 输出结束发送标志符
  printf("$PASSED$\n");
  xrt_putchar(4);
  _halt();
}

void secondary_main() {
  cpu_barrier_wait();
  xmain();
  cpu_barrier_wait();
  _halt();
}
