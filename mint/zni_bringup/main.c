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

// 以下几个 bar[4] 基地址的寄存器可以任意读写，可以作为 ram 进行测试
// the registers below based on bar[4] can be read/write randomly

#define ZNI_REG_RM_VP_TYPE 0x840
#define ZNI_REG_RM_MPQ_TYPE 0x850
#define ZNI_REG_RM_EQ_TYPE 0x860
#define ZNI_REG_RM_ATT_BASE 0x870

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

  if (zni->resources[0].flags == 0 || zni->resources[2].flags == 0 ||
      zni->resources[4].flags == 0) {
    printf("unexpected resources\n");
    xrt_exit(1);
  }

  printf("zni device %x vendor %x\n", zni->device, zni->vendor);

  void *vp_base = (void *)zni->resources[0].start;
  void *hdq_base = (void *)zni->resources[2].start;
  void *reg_base = (void *)zni->resources[4].start;

  // use these 4 registers as ram
  void *vp_type = reg_base + ZNI_REG_RM_VP_TYPE;
  void *mpq_type = reg_base + ZNI_REG_RM_MPQ_TYPE;
  void *eq_type = reg_base + ZNI_REG_RM_EQ_TYPE;
  void *attr_base = reg_base + ZNI_REG_RM_ATT_BASE;

  writeq(0x1111111111111111, vp_type);
  writeq(0x2222222222222222, mpq_type);
  writeq(0x3333333333333333, eq_type);
  writeq(0x4444444444444444, attr_base);

  printf("vp type %lx, mpq type %lx, eq type %lx, attr base %lx\n",
         readq(vp_type), readq(mpq_type), readq(eq_type), readq(attr_base));
}

void xmain() {
  int this_cpu = xrt_get_core_id();
  if (this_cpu == 0) {
    zni_bringup_main();
  }
}
