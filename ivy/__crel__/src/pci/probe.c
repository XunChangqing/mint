#include <asm/io.h>
#include <ivy/pci.h>
#include <ivy/print.h>
#include <linux/kernel.h>

#include "ivy_dt.h"

static __always_inline void pci_config_write_8(struct pci_dev *dev, int where,
                                               uint8_t v) {
  void *addr = pci_ecam_map_bus((void *)dev->bus->root_bridge->host->cfg_base,
                                dev->bus->number, dev->devfn, where);
  writeb(v, addr);
}

static __always_inline void pci_config_write_16(struct pci_dev *dev, int where,
                                                uint16_t v) {
  void *addr = pci_ecam_map_bus((void *)dev->bus->root_bridge->host->cfg_base,
                                dev->bus->number, dev->devfn, where);
  writew(v, addr);
}

static __always_inline void pci_config_write_32(struct pci_dev *dev, int where,
                                                uint32_t v) {
  void *addr = pci_ecam_map_bus((void *)dev->bus->root_bridge->host->cfg_base,
                                dev->bus->number, dev->devfn, where);
  writel(v, addr);
}

static __always_inline void pci_config_read_8(struct pci_dev *dev, int where,
                                              uint8_t *v) {
  void *addr = pci_ecam_map_bus((void *)dev->bus->root_bridge->host->cfg_base,
                                dev->bus->number, dev->devfn, where);
  *v = readb(addr);
}

static __always_inline void pci_config_read_16(struct pci_dev *dev, int where,
                                               uint16_t *v) {
  void *addr = pci_ecam_map_bus((void *)dev->bus->root_bridge->host->cfg_base,
                                dev->bus->number, dev->devfn, where);
  *v = readw(addr);
}

static __always_inline void pci_config_read_32(struct pci_dev *dev, int where,
                                               uint32_t *v) {
  void *addr = pci_ecam_map_bus((void *)dev->bus->root_bridge->host->cfg_base,
                                dev->bus->number, dev->devfn, where);
  *v = readl(addr);
}

static __always_inline void pci_bus_write_config_8(struct pci_bus *bus,
                                                   unsigned int devfn,
                                                   int where, uint8_t v) {
  void *addr = pci_ecam_map_bus((void *)bus->root_bridge->host->cfg_base,
                                bus->number, devfn, where);
  writeb(v, addr);
}

static __always_inline void pci_bus_write_config_16(struct pci_bus *bus,
                                                    unsigned int devfn,
                                                    int where, uint16_t v) {
  void *addr = pci_ecam_map_bus((void *)bus->root_bridge->host->cfg_base,
                                bus->number, devfn, where);
  writew(v, addr);
}

static __always_inline int pci_bus_write_config_32(struct pci_bus *bus,
                                                   unsigned int devfn,
                                                   int where, uint32_t v) {
  void *addr = pci_ecam_map_bus((void *)bus->root_bridge->host->cfg_base,
                                bus->number, devfn, where);
  writel(v, addr);
}

static __always_inline void pci_bus_read_config_8(struct pci_bus *bus,
                                                  unsigned int devfn, int where,
                                                  uint8_t *v) {
  void *addr = pci_ecam_map_bus((void *)bus->root_bridge->host->cfg_base,
                                bus->number, devfn, where);
  *v = readb(addr);
}

static __always_inline void pci_bus_read_config_16(struct pci_bus *bus,
                                                   unsigned int devfn,
                                                   int where, uint16_t *v) {
  void *addr = pci_ecam_map_bus((void *)bus->root_bridge->host->cfg_base,
                                bus->number, devfn, where);
  *v = readw(addr);
}

static __always_inline int pci_bus_read_config_32(struct pci_bus *bus,
                                                  unsigned int devfn, int where,
                                                  uint32_t *v) {
  void *addr = pci_ecam_map_bus((void *)bus->root_bridge->host->cfg_base,
                                bus->number, devfn, where);
  *v = readl(addr);
}

#define for_each_pci_bridge(dev, bus, iter)                           \
  for (int iter = 0, dev = &bus->devices[0]; iter < bus->num_devices; \
       iter += 1, dev += 1)                                           \
    if (!pci_is_bridge(dev)) {                                        \
    } else

// #define for_each_pci_dev(dev, bus, iter)                     \
//   for (int iter = 0, struct pci_dev *dev = &bus->devices[0]; \
//        iter < bus->num_devices; iter += 1, dev += 1)

#define MAX_NUM_PCI_DEVS (256)
#define MAX_NUM_PCI_BUSES (256)

unsigned int num_pci_devs = 0;
struct pci_dev pci_dev_store[MAX_NUM_PCI_DEVS] = {0};
unsigned int num_pci_buses = 0;
struct pci_bus pci_bus_store[MAX_NUM_PCI_BUSES] = {0};

#define MAX_NUM_PCI_ROOT_BRIDGE (32)
unsigned int num_pci_root_bridge = 0;
struct pci_root_bridge pci_root_bridge_store[MAX_NUM_PCI_ROOT_BRIDGE] = {0};

struct pci_dev *alloc_pci_dev() {
  if (num_pci_devs >= MAX_NUM_PCI_DEVS) {
    printf("failed to allocate pci dev\n");
    xrt_exit(1);
  }

  struct pci_dev *ret = &pci_dev_store[num_pci_devs];
  num_pci_devs += 1;
  return ret;
}

struct pci_bus *alloc_pci_bus() {
  if (num_pci_buses >= MAX_NUM_PCI_BUSES) {
    printf("failed to allocate pci bus\n");
    xrt_exit(1);
  }
  struct pci_bus *ret = &pci_bus_store[num_pci_buses];
  num_pci_buses += 1;
  return ret;
}

struct pci_root_bridge *alloc_pci_root_bridge() {
  if (num_pci_root_bridge >= MAX_NUM_PCI_ROOT_BRIDGE) {
    printf("failed to allocate pci root bridge\n");
    xrt_exit(1);
  }
  struct pci_root_bridge *ret = &pci_root_bridge_store[num_pci_root_bridge];
  num_pci_root_bridge += 1;
  return ret;
}

void pci_bus_add_dev(struct pci_bus *bus, struct pci_dev *dev) {
  if (bus->num_devices > MAX_NUM_CHILDREN) {
    printf("failed to pci_bus_add_dev\n");
    xrt_exit(1);
  }

  bus->devices[bus->num_devices] = dev;
  bus->num_devices += 1;
}

void pci_bus_add_child(struct pci_bus *bus, struct pci_bus *child) {
  if (bus->num_children > MAX_NUM_CHILDREN) {
    printf("failed to pci_bus_add_child\n");
    xrt_exit(1);
  }

  bus->children[bus->num_children] = child;
  bus->num_children += 1;
}

int pci_busnr_max;
uint64_t pci_io_base;
uint64_t pci_io_limit;
uint64_t pci_mem32_base;
uint64_t pci_mem32_limit;
uint64_t pci_mem64_base;
uint64_t pci_mem64_limit;

static uint64_t pci_size(uint64_t maxbase, uint64_t mask) {
  uint64_t size = mask & maxbase; /* Find the significant bits */
  if (!size) return 0;

  /*
   * Get the lowest of them to find the decode size, and from that
   * the extent.
   */
  size = size & ~(size - 1);

  return size;
}

static inline unsigned long decode_bar(struct pci_dev *dev, uint32_t bar) {
  uint32_t mem_type;
  unsigned long flags;

  if ((bar & PCI_BASE_ADDRESS_SPACE) == PCI_BASE_ADDRESS_SPACE_IO) {
    flags = bar & ~PCI_BASE_ADDRESS_IO_MASK;
    flags |= IORESOURCE_IO;
    return flags;
  }

  flags = bar & ~PCI_BASE_ADDRESS_MEM_MASK;
  flags |= IORESOURCE_MEM;
  if (flags & PCI_BASE_ADDRESS_MEM_PREFETCH) flags |= IORESOURCE_PREFETCH;

  mem_type = bar & PCI_BASE_ADDRESS_MEM_TYPE_MASK;
  switch (mem_type) {
    case PCI_BASE_ADDRESS_MEM_TYPE_32:
      break;
    case PCI_BASE_ADDRESS_MEM_TYPE_1M:
      /* 1M mem BAR treated as 32-bit BAR */
      break;
    case PCI_BASE_ADDRESS_MEM_TYPE_64:
      flags |= IORESOURCE_MEM_64;
      break;
    default:
      /* mem unknown type treated as 32-bit BAR */
      break;
  }
  return flags;
}

static int pci_config_base(struct pci_dev *dev, unsigned int pos,
                           struct resource *res) {
  uint32_t l = 0, sz = 0, mask;
  uint64_t l64, sz64, mask64;
  // uint16_t orig_cmd;
  // struct pci_bus_region region, inverted_region;

  mask = ~0;

  pci_config_write_32(dev, pos, mask);
  pci_config_read_32(dev, pos, &sz);

  res->flags = decode_bar(dev, sz);
  //   printf("pos %d, sz %x, flags %x\n", pos, sz, res->flags);
  res->flags |= IORESOURCE_SIZEALIGN;
  if (res->flags & IORESOURCE_IO) {
    sz64 = sz & PCI_BASE_ADDRESS_IO_MASK;
    mask64 = PCI_BASE_ADDRESS_IO_MASK & (uint32_t)IO_SPACE_LIMIT;
  } else {
    sz64 = sz & PCI_BASE_ADDRESS_MEM_MASK;
    mask64 = (uint32_t)PCI_BASE_ADDRESS_MEM_MASK;
  }

  if (res->flags & IORESOURCE_MEM_64) {
    pci_config_write_32(dev, pos + 4, ~0);
    pci_config_read_32(dev, pos + 4, &sz);

    sz64 |= ((uint64_t)sz << 32);
    mask64 |= ((uint64_t)~0 << 32);
  }

  // printf("sz64 %lx, mask64 %x\n", sz64, mask64);

  if (!sz64) goto fail;

  sz64 = pci_size(sz64, mask64);

  if (!sz64) {
    printf("reg 0x%x: invalid BAR (can't size)\n", pos);
    xrt_exit(1);
  }

  uint64_t sz64m1 = sz64 - 1;
  uint64_t align_mask = ~sz64m1;

  //   bool is_nvme = false;
  //   if (dev->class == 0x10802) {
  //     is_nvme = true;
  //     printf("sz64 %lx\n", sz64);
  //   }

  // roundup to the size of bar
  if (res->flags & IORESOURCE_MEM_64) {
    uint64_t bar = (pci_mem64_base + sz64m1) & align_mask;
    pci_mem64_base = bar + sz64;
    pci_config_write_32(dev, pos, (uint32_t)bar);
    pci_config_write_32(dev, pos + 4, (uint32_t)(bar >> 32));
    res->start = bar;
    res->end = bar + sz64 - 1;
    // if (is_nvme) {
    //   printf("is nvme %d\n", pos);
    // }

  } else if (res->flags & IORESOURCE_MEM) {
    uint64_t bar = (pci_mem32_base + sz64m1) & align_mask;
    pci_mem32_base = bar + sz64;
    pci_config_write_32(dev, pos, (uint32_t)bar);
    res->start = bar;
    res->end = bar + sz64 - 1;

  } else if (res->flags & IORESOURCE_IO) {
    uint64_t bar = (pci_io_base + sz64m1) & align_mask;
    pci_io_base = bar + sz64;
    pci_config_write_32(dev, pos, (uint32_t)bar);
    res->start = bar;
    res->end = bar + sz64 - 1;
  } else {
    printf("unsupported resource type!\n");
    xrt_exit(1);
  }

  goto out;

fail:
  res->flags = 0;

out:
  return (res->flags & IORESOURCE_MEM_64) ? 1 : 0;
}

static void pci_config_bases(struct pci_dev *dev, unsigned int howmany) {
  //   printf("pci_config_bases howmany %d\n", howmany);
  unsigned int pos, reg;
  for (pos = 0; pos < howmany; pos++) {
    struct resource *res = &dev->resources[pos];
    reg = PCI_BASE_ADDRESS_0 + (pos << 2);
    pos += pci_config_base(dev, reg, res);
  }
}

void pci_setup_device(struct pci_dev *dev) {
  uint32_t device_id;
  uint32_t vendor_id;
  pci_config_read_32(dev, PCI_VENDOR_ID, &device_id);
  vendor_id = device_id & 0xFFFF;
  device_id = device_id >> 16;

  dev->device = (unsigned short)device_id;
  dev->vendor = (unsigned short)vendor_id;
  //   printf("device id %x vendor id %x\n", dev->device, dev->vendor);

  uint32_t class_code;
  uint32_t rev_id;
  pci_config_read_32(dev, PCI_CLASS_REVISION, &class_code);

  rev_id = class_code & 0xFF;
  class_code = class_code >> 8;

  dev->class = class_code;
  dev->revision = rev_id;
  //   printf("class %x rev %x\n", dev->class, dev->revision);

  uint8_t hdr_type;
  pci_config_read_8(dev, PCI_HEADER_TYPE, &hdr_type);
  dev->hdr_type = hdr_type;
  //   printf("hdr_type %x\n", pdev->hdr_type);
  bool is_multi_fn = hdr_type & 0x80;
  hdr_type = hdr_type & PCI_HEADER_TYPE_MASK;

  switch (hdr_type) {            /* header type */
    case PCI_HEADER_TYPE_NORMAL: /* standard header */
      pci_config_bases(dev, 6);
      break;

    case PCI_HEADER_TYPE_BRIDGE: /* bridge header */
      pci_config_bases(dev, 2);
      break;

    default:
      break;
  }

  pci_config_write_16(dev, PCI_COMMAND,
                      PCI_COMMAND_IO | PCI_COMMAND_MEMORY | PCI_COMMAND_MASTER);
}

void pci_scan_child_bus(struct pci_bus *bus);

static void pci_setup_bridge_io(struct pci_dev *bridge, uint64_t base,
                                uint64_t limit) {
  // struct resource *res;
  // struct pci_bus_region region;
  unsigned long io_mask;
  uint8_t io_base_lo, io_limit_lo;
  uint16_t l;
  uint32_t io_upper16;

  io_mask = PCI_IO_RANGE_MASK;
  // if (bridge->io_window_1k)
  // 	io_mask = PCI_IO_1K_RANGE_MASK;

  /* Set up the top and bottom of the PCI I/O segment for this bus */
  // res = &bridge->resource[PCI_BRIDGE_IO_WINDOW];
  // pcibios_resource_to_bus(bridge->bus, &region, res);
  // if (res->flags & IORESOURCE_IO) {
  pci_config_read_16(bridge, PCI_IO_BASE, &l);
  io_base_lo = (base >> 8) & io_mask;
  io_limit_lo = (limit >> 8) & io_mask;
  l = ((uint16_t)io_limit_lo << 8) | io_base_lo;
  /* Set up upper 16 bits of I/O base/limit */
  io_upper16 = (limit & 0xffff0000) | (base >> 16);
  // pci_info(bridge, "  bridge window %pR\n", res);
  // } else {
  // 	/* Clear upper 16 bits of I/O base/limit */
  // 	io_upper16 = 0;
  // 	l = 0x00f0;
  // }
  /* Temporarily disable the I/O range before updating PCI_IO_BASE */
  pci_config_write_32(bridge, PCI_IO_BASE_UPPER16, 0x0000ffff);
  /* Update lower 16 bits of I/O base/limit */
  pci_config_write_16(bridge, PCI_IO_BASE, l);
  /* Update upper 16 bits of I/O base/limit */
  pci_config_write_32(bridge, PCI_IO_BASE_UPPER16, io_upper16);
}

static void pci_setup_bridge_mmio(struct pci_dev *bridge, uint64_t base,
                                  uint64_t limit) {
  //   struct resource *res;
  //   struct pci_bus_region region;
  uint32_t l;

  /* Set up the top and bottom of the PCI Memory segment for this bus */
  // res = &bridge->resource[PCI_BRIDGE_MEM_WINDOW];
  // pcibios_resource_to_bus(bridge->bus, &region, res);
  // if (res->flags & IORESOURCE_MEM) {
  l = (base >> 16) & 0xfff0;
  l |= limit & 0xfff00000;
  //   pci_info(bridge, "  bridge window %pR\n", res);
  // } else {
  // 	l = 0x0000fff0;
  // }
  pci_config_write_32(bridge, PCI_MEMORY_BASE, l);
}

static void pci_setup_bridge_mmio_64(struct pci_dev *bridge, uint64_t base,
                                     uint64_t limit) {
  //   struct resource *res;
  //   struct pci_bus_region region;
  uint32_t l, bu, lu;

  /*
   * Clear out the upper 32 bits of PREF limit.  If
   * PCI_PREF_BASE_UPPER32 was non-zero, this temporarily disables
   * PREF range, which is ok.
   */
  pci_config_write_32(bridge, PCI_PREF_LIMIT_UPPER32, 0);

  /* Set up PREF base/limit */
  bu = lu = 0;
  //   res = &bridge->resource[PCI_BRIDGE_PREF_MEM_WINDOW];
  //   pcibios_resource_to_bus(bridge->bus, &region, res);
  //   if (res->flags & IORESOURCE_PREFETCH) {
  l = (base >> 16) & 0xfff0;
  l |= limit & 0xfff00000;
  // if (res->flags & IORESOURCE_MEM_64) {
  bu = upper_32_bits(base);
  lu = upper_32_bits(limit);
  // }
  // pci_info(bridge, "  bridge window %pR\n", res);
  //   } else {
  //     l = 0x0000fff0;
  //   }
  pci_config_write_32(bridge, PCI_PREF_MEMORY_BASE, l);

  /* Set the upper 32 bits of PREF base & limit */
  pci_config_write_32(bridge, PCI_PREF_BASE_UPPER32, bu);
  pci_config_write_32(bridge, PCI_PREF_LIMIT_UPPER32, lu);
}

/*
 * pci_scan_bridge() - Scan buses behind a bridge
 * @bus: Parent bus the bridge is on
 * @dev: Bridge itself
 * @max: Starting subordinate number of buses behind this bridge
 *
 * If it's a bridge, configure it and scan the bus behind it.
 * For CardBus bridges, we don't scan behind as the devices will
 * be handled by the bridge driver itself.
 *
 * Return: New subordinate number covering all buses behind this bridge.
 */
void pci_scan_bridge(struct pci_bus *bus, struct pci_dev *dev) {
  struct pci_bus *child;
  int is_cardbus = (dev->hdr_type == PCI_HEADER_TYPE_CARDBUS);
  uint32_t buses = 0;

  child = alloc_pci_bus();
  dev->subordinate = child;
  child->root_bridge = bus->root_bridge;
  child->parent = bus;
  child->self = dev;
  pci_busnr_max += 1;
  child->number = pci_busnr_max;
  child->primary = bus->number;
  pci_bus_add_child(bus, child);

  buses = ((unsigned int)(child->primary) << 0) |
          ((unsigned int)(child->number) << 8) | ((unsigned int)(0xFF) << 16);
  /* We need to blast all three values with a single write */
  pci_config_write_32(dev, PCI_PRIMARY_BUS, buses);

  // 简单起见，不论 bridge 以下有没有设备，全部向上对齐
  uint64_t io_window_sz = 1 << 12;  // 4KB
  uint64_t io_window_szm1 = io_window_sz - 1;
  uint64_t io_window_align_mask = ~io_window_szm1;
  uint64_t mem_window_sz = 1 << 20;  // 1MB
  uint64_t mem_window_szm1 = mem_window_sz - 1;
  uint64_t mem_window_align_mask = ~mem_window_szm1;

  pci_io_base = (pci_io_base + io_window_szm1) & io_window_align_mask;
  pci_mem32_base = (pci_mem32_base + mem_window_szm1) & mem_window_align_mask;
  pci_mem64_base = (pci_mem64_base + mem_window_szm1) & mem_window_align_mask;

  uint64_t io_base = pci_io_base;
  uint64_t mem32_base = pci_mem32_base;
  uint64_t mem64_base = pci_mem64_base;

  pci_scan_child_bus(child);

  uint64_t io_limit, mem32_limit, mem64_limit;

  if (pci_io_base <= io_base) {
    io_base = 0;
    io_limit = 0;
  } else {
    // 向上对齐
    io_limit = (pci_io_base + io_window_szm1) & io_window_align_mask;
    io_limit = io_limit - 1;
  }
  if (pci_mem32_base <= mem32_base) {
    mem32_base = 0;
    mem32_limit = 0;
  } else {
    mem32_limit = (pci_mem32_base + mem_window_szm1) & mem_window_align_mask;
    mem32_limit = mem32_limit - 1;
  }
  if (pci_mem64_base <= mem64_base) {
    mem64_base = 0;
    mem64_limit = 0;
  } else {
    mem64_limit = (pci_mem64_base + mem_window_szm1) & mem_window_align_mask;
    mem64_limit = mem64_limit - 1;
  }

  printf("setup bridge, bus id %d\n", bus->number);
  printf("io base %lx limit %lx\n", io_base, io_limit);
  printf("mem32 base %lx limit %lx\n", mem32_base, mem32_limit);
  printf("mem64 base %lx limit %lx\n", mem64_base, mem64_limit);

  pci_setup_bridge_io(dev, io_base, io_limit);
  pci_setup_bridge_mmio(dev, mem32_base, mem32_limit);
  pci_setup_bridge_mmio_64(dev, mem64_base, mem64_limit);

  /*
   * Set subordinate bus number to its real value.
   */
  pci_config_write_8(dev, PCI_SUBORDINATE_BUS, pci_busnr_max);

  // out:
  //   pci_config_write_16(dev, PCI_BRIDGE_CONTROL, PCI_BRIDGE_CTL_BUS_RESET);
}

/**
 * pci_scan_child_bus() - Scan devices below a bus
 * @bus: Bus to scan for devices
 *
 * Scans devices below @bus including subordinate buses. Returns new
 * subordinate number including all the found devices.
 *
 * Return: New subordinate number covering all buses under this bus.
 */
void pci_scan_child_bus(struct pci_bus *bus) {
  // scan only one function each device
  for (unsigned int devfn = 0; devfn < 256; devfn += 8) {
    uint32_t device_id;
    uint32_t vendor_id;
    pci_bus_read_config_32(bus, devfn, PCI_VENDOR_ID, &device_id);
    vendor_id = device_id & 0xFFFF;
    device_id = device_id >> 16;

    if (vendor_id == 0xFFFF || device_id == 0xFFFF) {
      continue;
    }
    // printf("valid device device id %x vendor id %x\n", device_id, vendor_id);

    struct pci_dev *ndev = alloc_pci_dev();
    ndev->bus = bus;
    ndev->devfn = devfn;
    // printf("dev addr %lx\n", ndev);
    pci_setup_device(ndev);
    pci_bus_add_dev(bus, ndev);
  }

  // printf("bus number devices %d\n", bus->num_devices);

  // scan and configure subodinate buses
  // 扫描子总线，并分配 bus 编号
  for (int iter = 0; iter < bus->num_devices; iter++) {
    struct pci_dev *dev = bus->devices[iter];
    // printf("dev addr %lx\n", dev);
    printf("device %x, vendor %x, class %x, header %x, devfn %x\n", dev->device,
           dev->vendor, dev->class, dev->hdr_type, dev->devfn);

    if (pci_is_bridge(dev)) {
      printf("scan bridge %x\n", dev->device);
      pci_scan_bridge(bus, dev);
    }
  }
}

// 重新枚举并配置指定 host 下所有 pci 设备，暂时未考虑 hot-plug 需求
// 虽然 uboot 一般会枚举和配置， 操作系统一般只需要枚举即可，不需要配置
// 但是考虑两个情况的需求，还是完全重新配置
// 1. 软仿下不会运行 uboot
// 2. qemu 中使用 direct kernel boot 时，也不会运行 uboot
void pci_host_probe(struct dt_pci_host *phost) {
  struct pci_root_bridge *root_bridge = alloc_pci_root_bridge();
  root_bridge->host = phost;
  // printf("scan pci host %s\n", ph->name);
  struct pci_bus *root_bus = alloc_pci_bus();
  root_bus->root_bridge = root_bridge;
  root_bus->number = 0;
  root_bridge->bus = root_bus;

  pci_busnr_max = 0;
  // 为所属设备分配资源（bar），并设置所有总线资源
  pci_io_base = phost->io_base;
  pci_mem32_base = phost->mem32_base;
  pci_mem64_base = phost->mem64_base;

  //   pci_io_limit = phost->io_size;
  //   pci_mem32_limit = phost->mem32_size;
  //   pci_mem64_limit = phost->mem64_size;

  pci_scan_child_bus(root_bus);
}

void pci_host_probe_all() {
  for (int i = 0; i < IVY_DT_NUM_PCI_HOST; i++) {
    struct dt_pci_host *ph = &ivy_dt_pci_hosts[i];
    pci_host_probe(ph);
  }
}

void pci_foreach_device(pci_dev_cb cb, void *user_data) {
  int bqp = 0;
  struct pci_bus *bus_q[MAX_NUM_PCI_BUSES] = {NULL};
  for (int i = 0; i < num_pci_root_bridge; i++) {
    bus_q[bqp] = pci_root_bridge_store[i].bus;
    bqp++;
  }

  //   printf("root bridges %d\n", num_pci_root_bridge);

  while (bqp > 0) {
    struct pci_bus *bus = bus_q[bqp - 1];
    bqp--;
    printf("traverse bus, num devices %d\n", bus->num_devices);
    for (int di = 0; di < bus->num_devices; di++) {
      struct pci_dev *dev = bus->devices[di];

      if (cb(dev, user_data)) {
        return;
      }

      if (dev->subordinate) {
        bus_q[bqp] = dev->subordinate;
        bqp++;
      }
    }
  }
}
