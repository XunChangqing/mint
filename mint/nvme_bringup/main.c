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

bool find_a_nvme(struct pci_dev *dev, void *user_data) {
  if (pci_dev_is_nvme(dev)) {
    struct pci_dev **pud = (struct pci_dev **)(user_data);
    *pud = dev;
    return true;
  }
  return false;
}

void zni_bringup_main() {
  printf("hello world from nvme_bringup\n");

  pci_host_probe_all();
  printf("probe over\n");

  struct pci_dev *nvme = NULL;
  pci_foreach_device(find_a_nvme, &nvme);

  if (nvme == NULL) {
    printf("no nvme exists\n");
    xrt_exit(1);
  }

  printf("got a nvme device %x vendor %x\n", nvme->device, nvme->vendor);

  struct nvme_bar *nvme_bar = (struct nvme_bar *)nvme->resources[0].start;
  uint64_t nvme_cap = nvme_readq(&nvme_bar->cap);
  uint32_t nvme_vs = readl(&nvme_bar->vs);
  printf("nvme cap %lx version %x\n", nvme_cap, nvme_vs);

  struct nvme_dev *nvme_dev = malloc(sizeof(struct nvme_dev));
  printf("nvme init\n");
  nvme_init(nvme_dev, nvme);

  if (list_empty(&nvme_dev->namespaces)) {
    printf("no active namespace\n");
  } else {
    struct nvme_ns *nvme_ns =
        list_first_entry(&nvme_dev->namespaces, struct nvme_ns, list);
    printf("nvme ns id %d, log2blksz %d\n", nvme_ns->ns_id, nvme_ns->lba_shift);

    unsigned int blksz = 1 << nvme_ns->lba_shift;
    char *src_blk_buf = malloc(blksz);
    char *dst_blk_buf = malloc(blksz);
    for (int i = 0; i < blksz; i++) {
      src_blk_buf[i] = i;
    }

    printf("nvme block read and write\n");
    nvme_blk_write(nvme_ns, 0, 1, src_blk_buf);
    nvme_blk_read(nvme_ns, 0, 1, dst_blk_buf);
    for (int i = 0; i < blksz; i++) {
      if ((char)i != dst_blk_buf[i]) {
        printf("blk read&write error %d %d\n", i, dst_blk_buf[i]);
      }
    }
  }
}

void xmain() {
  int this_cpu = xrt_get_core_id();
  if (this_cpu == 0) {
    zni_bringup_main();
  }
}
