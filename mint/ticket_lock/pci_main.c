// author : zuoqian
// Copyright 2024. All rights reserved.

#include <ivy/halt_code.h>
#include <ivy/nvme.h>
#include <ivy/pci.h>
#include <ivy/print.h>
#include <ivy/sync.h>
#include <ivy/xrt.h>
#include <ivy/zni.h>

#include "ivy_cfg.h"
#include "ivy_dt.h"

uint64_t counter_v;
uint64_t *counter = &counter_v;

bool find_a_zni(struct pci_dev *dev, void *user_data) {
  if (pci_dev_is_zni(dev)) {
    struct pci_dev **pud = (struct pci_dev **)(user_data);
    *pud = dev;
    return true;
  }
  return false;
}

// 这两个寄存器可任意读写，作为ram测试
// __u64 asq;   /* Admin SQ Base Address */
// __u64 acq;   /* Admin CQ Base Address */
bool find_a_nvme(struct pci_dev *dev, void *user_data) {
  if (pci_dev_is_nvme(dev)) {
    struct pci_dev **pud = (struct pci_dev **)(user_data);
    *pud = dev;
    return true;
  }
  return false;
}

void use_zni() {
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

  WRITE_ONCE(counter, (uint64_t *)mpq_type);
}

void use_nvme() {
  struct pci_dev *nvme = NULL;
  pci_foreach_device(find_a_nvme, &nvme);

  if (nvme == NULL) {
    printf("no nvme exists\n");
    xrt_exit(1);
  }

  printf("got a nvme device %x vendor %x\n", nvme->device, nvme->vendor);

  struct nvme_bar *nvme_bar = (struct nvme_bar *)nvme->resources[0].start;

  //   nvme_bar->acq;
  //   nvme_bar->asq;
  //   counter = (uint64_t *)&(nvme_bar->acq);
  WRITE_ONCE(counter, (uint64_t *)&(nvme_bar->acq));
}

void init() {
  pci_host_probe_all();

#ifdef USE_NVME
  printf("use nvme\n");
  use_nvme();
#elif USE_ZNI
  printf("use zni\n");
  use_zni();
#endif
}

void mango_core_main_func(uint64_t core_id);

void xmain() {
  int this_cpu = xrt_get_core_id();
  if (this_cpu == 0) {
    init();
  }
  cpu_barrier_wait();
  mango_core_main_func(xrt_get_core_id());
}
