// author : zuoqian
// Copyright 2024. All rights reserved.

#include <asm/io.h>
#include <ivy/halt_code.h>
#include <ivy/nvme.h>
#include <ivy/pci.h>
#include <ivy/print.h>
#include <ivy/xrt.h>
#include <linux/atomic.h>
#include <stdint.h>

#include "ivy_cfg.h"
#include "ivy_dt.h"

bool print_dev(struct pci_dev *dev, void *user_data) {
  printf("pci dev bus %d devfn %x device %x vendor %x class %x\n",
         dev->bus->number, dev->devfn, dev->device, dev->vendor, dev->class);
  for (int i = 0; i < 6; i++) {
    struct resource *res = &dev->resources[i];
    if (res->flags) {
      printf("res %d flags %x start %lx end %lx\n", i, res->flags, res->start,
             res->end);
    }
  }
  return false;
}

bool find_a_nvme(struct pci_dev *dev, void *user_data) {
  if (pci_dev_is_nvme(dev)) {
    struct pci_dev **pud = (struct pci_dev **)(user_data);
    *pud = dev;
    return true;
  }
  return false;
}

bool find_a_zni(struct pci_dev *dev, void *user_data) {
  if (pci_dev_is_zni(dev)) {
    struct pci_dev **pud = (struct pci_dev **)(user_data);
    *pud = dev;
    return true;
  }
  return false;
}

#include <ivy/malloc.h>

void zni_bringup_main() {
  printf("hello world from pci_bringup\n");

  void *p = malloc(1024);

  pci_host_probe_all();
  printf("probe over\n");

  pci_foreach_device(print_dev, NULL);

  struct pci_dev *nvme = NULL;
  pci_foreach_device(find_a_nvme, &nvme);
  if (nvme != NULL) {
    printf("got a nvme %x %x\n", nvme->device, nvme->vendor);

    struct nvme_bar *nvme_bar = (struct nvme_bar *)nvme->resources[0].start;
    uint64_t nvme_cap = nvme_readq(&nvme_bar->cap);
    uint32_t nvme_vs = readl(&nvme_bar->vs);
    printf("nvme cap %lx version %x\n", nvme_cap, nvme_vs);

    // asq基地址可以作为一个设备 ram 随意读写
    nvme_writeq(0x1234567887654321, &nvme_bar->asq);
    uint64_t asq;
    asq = nvme_readq(&nvme_bar->asq);
    printf("asq %lx\n", asq);

    struct nvme_dev *nvme_dev = malloc(sizeof(struct nvme_dev));
    printf("nvme init\n");
    nvme_init(nvme_dev, nvme);

    if (list_empty(&nvme_dev->namespaces)) {
      printf("no active namespace\n");
    } else {
      struct nvme_ns *nvme_ns =
          list_first_entry(&nvme_dev->namespaces, struct nvme_ns, list);
      printf("nvme ns id %d, log2blksz %d\n", nvme_ns->ns_id,
             nvme_ns->lba_shift);

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

  struct pci_dev *zni = NULL;
  pci_foreach_device(find_a_zni, &zni);
  if (zni != NULL) {
    printf("got a zni %x %x\n", zni->device, zni->vendor);
  }

  malloc_simple_info();
}

void xmain() {
  int this_cpu = xrt_get_core_id();
  if (this_cpu == 0) {
    zni_bringup_main();
  }
}
