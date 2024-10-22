#pragma once

#include <ivy/pci_regs.h>
#include <stdint.h>

/*
 * IO resources have these defined flags.
 *
 * PCI devices expose these flags to userspace in the "resource" sysfs file,
 * so don't move them.
 */
#define IORESOURCE_BITS 0x000000ff /* Bus-specific bits */

#define IORESOURCE_TYPE_BITS 0x00001f00 /* Resource type */
#define IORESOURCE_IO 0x00000100        /* PCI/ISA I/O ports */
#define IORESOURCE_MEM 0x00000200
#define IORESOURCE_REG 0x00000300 /* Register offsets */
#define IORESOURCE_IRQ 0x00000400
#define IORESOURCE_DMA 0x00000800
#define IORESOURCE_BUS 0x00001000

#define IORESOURCE_PREFETCH 0x00002000 /* No side effects */
#define IORESOURCE_READONLY 0x00004000
#define IORESOURCE_CACHEABLE 0x00008000
#define IORESOURCE_RANGELENGTH 0x00010000
#define IORESOURCE_SHADOWABLE 0x00020000

#define IORESOURCE_SIZEALIGN 0x00040000  /* size indicates alignment */
#define IORESOURCE_STARTALIGN 0x00080000 /* start field is alignment */

#define IORESOURCE_MEM_64 0x00100000
#define IORESOURCE_WINDOW 0x00200000 /* forwarded by bridge */
#define IORESOURCE_MUXED 0x00400000  /* Resource is software muxed */

/*
 * Enhanced Configuration Access Mechanism (ECAM)
 *
 * See PCI Express Base Specification, Revision 5.0, Version 1.0,
 * Section 7.2.2, Table 7-1, p. 677.
 */
#define PCIE_ECAM_BUS_SHIFT 20   /* Bus number */
#define PCIE_ECAM_DEVFN_SHIFT 12 /* Device and Function number */

#define PCIE_ECAM_BUS_MASK 0xff
#define PCIE_ECAM_DEVFN_MASK 0xff
#define PCIE_ECAM_REG_MASK 0xfff /* Limit offset to a maximum of 4K */

#define PCIE_ECAM_BUS(x) (((x)&PCIE_ECAM_BUS_MASK) << PCIE_ECAM_BUS_SHIFT)
#define PCIE_ECAM_DEVFN(x) (((x)&PCIE_ECAM_DEVFN_MASK) << PCIE_ECAM_DEVFN_SHIFT)
#define PCIE_ECAM_REG(x) ((x)&PCIE_ECAM_REG_MASK)

#define PCIE_ECAM_OFFSET(bus, devfn, where) \
  (PCIE_ECAM_BUS(bus) | PCIE_ECAM_DEVFN(devfn) | PCIE_ECAM_REG(where))

static __always_inline void __iomem *pci_ecam_map_bus(void *base,
                                                      unsigned int bus_num,
                                                      unsigned int devfn,
                                                      int where) {
  // bus_shift must be 0
  return base + PCIE_ECAM_OFFSET(bus_num, devfn, where);
}

struct resource {
  uint64_t start;
  uint64_t end;
  unsigned long flags;
};

struct pci_bus;

struct pci_root_bridge {
  struct dt_pci_host *host;
  struct pci_bus *bus;
};

struct pci_dev {
  struct pci_bus *bus;         /* Bus this device is on */
  struct pci_bus *subordinate; /* Bus this device bridges to */
  uint32_t devfn;              /* Encoded device & function index */
  uint16_t vendor;
  uint16_t device;
  uint16_t subsystem_vendor;
  uint16_t subsystem_device;
  uint32_t class;   /* 3 bytes: (base,sub,prog-if) */
  uint8_t revision; /* PCI revision, low byte of class word */
  uint8_t hdr_type; /* PCI header type (`multi' flag masked out) */

  struct resource resources[6];
};

#define MAX_NUM_CHILDREN (16)

struct pci_bus {
  // no pci_dev for root bus, and fast root bridge access for sub-buses
  struct pci_root_bridge *root_bridge;
  struct pci_bus *parent;  // Parent bus this bridge is on
  unsigned int num_children;
  struct pci_bus *children[MAX_NUM_CHILDREN];  // array of child buses
  unsigned int num_devices;
  struct pci_dev *devices[MAX_NUM_CHILDREN];  // array of devices on this bus
  struct pci_dev *self;                       // Bridge device as seen by parent
  unsigned char number;                       /* Bus number */
  unsigned char primary;                      /* Number of primary bridge */
};

static inline bool pci_is_bridge(struct pci_dev *dev) {
  return dev->hdr_type == PCI_HEADER_TYPE_BRIDGE ||
         dev->hdr_type == PCI_HEADER_TYPE_CARDBUS;
}

typedef bool pci_dev_cb(struct pci_dev *, void *user_data);
void pci_foreach_device(pci_dev_cb cb, void *user_data);

void pci_host_probe_all();

static bool pci_dev_is_nvme(struct pci_dev *pdev) {
  // NVMe, class code
  // base-class 8, sub-class 8, programming interface 8
  // 01h, 08h, 02h, NVM Express I/O controller
  if (pdev->class == 0x010802) {
    return true;
  }
  return false;
}

static bool pci_dev_is_zni(struct pci_dev *pdev) {
  if (pdev->device == 0x6669 && pdev->vendor == 0x1619) {
    return true;
  }
  return false;
}
