// author : zuoqian
// Copyright 2024. All rights reserved.

#include <asm/io.h>
#include <ivy/halt_code.h>
#include <ivy/malloc.h>
#include <ivy/nvme.h>
#include <ivy/pci.h>
#include <ivy/print.h>
#include <ivy/xrt.h>
#include <linux/atomic.h>
#include <stdint.h>

#include "ivy_cfg.h"
#include "ivy_dt.h"

bool find_a_zni(struct pci_dev *dev, void *user_data) {
  if (pci_dev_is_zni(dev)) {
    struct pci_dev **pud = (struct pci_dev **)(user_data);
    *pud = dev;
    return true;
  }
  return false;
}

void zni_bringup_main() {
  printf("hello world from zni_bringup\n");

  pci_host_probe_all();
  printf("probe over\n");

  struct pci_dev *zni = NULL;
  pci_foreach_device(find_a_zni, &zni);
  if (zni == NULL) {
    printf("no zni exists\n");
    xrt_exit(1);
  }

  printf("zni device %x vendor %x\n", zni->device, zni->vendor);
}

void xmain() {
  int this_cpu = xrt_get_core_id();
  if (this_cpu == 0) {
    zni_bringup_main();
  }
}
