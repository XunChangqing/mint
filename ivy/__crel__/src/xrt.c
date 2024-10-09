#include <ivy/halt_code.h>
#include <ivy/xrt.h>

#include "ivy_dt.h"

#ifdef IVY_DT_STDOUT_PL011
#include "pl011.h"
#elif defined DT_STDOUT_DW16550
#include "dw16550.h"
#elif defined DT_STDOUT_DUMMY
#include "dummy_uart.h"
#endif

#include <ivy/print.h>
#include <ivy/sync.h>
#include <linux/spinlock.h>

DEFINE_SPINLOCK(exit_spin_lock);

void _error_halt(unsigned long halt_code);
// 直接当前核停止，不会参与end barrier，导致不能结束，不会输出 $PASSED$
void xrt_exit(unsigned long halt_code) {
  spin_lock(&exit_spin_lock);
  printf("halt code: %d\n", halt_code);
  printf("$FAILED$\n");
  // 不释放锁，只允许一个核报告Failed，其他核会卡住
  // spin_unlock(&exit_spin_lock);
  _error_halt(HALT_CODE_USER + halt_code);
}

void xrt_putchar(char c) {
#ifdef IVY_DT_STDOUT_PL011
  pl011_putchar(IVY_DT_STDOUT_PL011_BASE, c);
#elif defined DT_STDOUT_DW16550
  dw16550_putchar(DT_STDOUT_DW16550_BASE, c);
#elif defined DT_STDOUT_DUMMY
  dummy_uart_putchar(DT_STDOUT_DUMMY_BASE, c);
#else
#error stdout must be config
#endif
}
