// author : zuoqian
// Copyright 2024. All rights reserved.

#pragma once

#include <stdint.h>

// #define CL_0 (0x40000000)
// #define CL_1 (0x44080000)
// #define CL_2 (0x44480000)
// #define CL_3 (0x44880000)
#include "cl_def.h"
#include "print.h"
#include "xrt.h"

static inline void mem_write8(uintptr_t addr, uint8_t v) {
  volatile uint8_t *p = (uint8_t *)addr;
  *p = v;
}

static inline void mem_write16(uintptr_t addr, uint16_t v) {
  volatile uint16_t *p = (uint16_t *)addr;
  *p = v;
}

static inline void mem_write32(uintptr_t addr, uint32_t v) {
  volatile uint32_t *p = (uint32_t *)addr;
  *p = v;
}

static inline void mem_write64(uintptr_t addr, uint64_t v) {
  volatile uint64_t *p = (uint64_t *)addr;
  *p = v;
}

static inline void mem_write128(uintptr_t addr, uint64_t v0, uint64_t v1) {
  mem_write64(addr, v0);
  mem_write64(addr + 8, v1);
}

static inline void mem_write256(uintptr_t addr, uint64_t v0, uint64_t v1,
                                uint64_t v2, uint64_t v3) {
  mem_write128(addr, v0, v1);
  mem_write128(addr + 16, v2, v3);
}

static inline void mem_write512(uintptr_t addr, uint64_t v0, uint64_t v1,
                                uint64_t v2, uint64_t v3, uint64_t v4,
                                uint64_t v5, uint64_t v6, uint64_t v7) {
  mem_write256(addr, v0, v1, v2, v3);
  mem_write256(addr + 32, v4, v5, v6, v7);
}

static inline uint8_t mem_read8(uintptr_t addr) {
  volatile uint8_t *p = (uint8_t *)addr;
  return *p;
}
static inline uint16_t mem_read16(uintptr_t addr) {
  volatile uint16_t *p = (uint16_t *)addr;
  return *p;
}
static inline uint32_t mem_read32(uintptr_t addr) {
  volatile uint32_t *p = (uint32_t *)addr;
  return *p;
}
static inline uint64_t mem_read64(uintptr_t addr) {
  volatile uint64_t *p = (uint64_t *)addr;
  return *p;
}

static inline void mem_read_check8(uintptr_t addr, uint8_t v) {
  uint8_t v_dut = mem_read8(addr);
  if (v != v_dut) {
    printf("mem_read_check8 failed, addr: %lx, val_expected: %u, val_dut: %u\n",
           addr, v, v_dut);
    xrt_exit(1);
  }
}

static inline void mem_read_check16(uintptr_t addr, uint16_t v) {
  uint16_t v_dut = mem_read16(addr);
  if (v != v_dut) {
    printf(
        "mem_read_check16 failed, addr: %lx, val_expected: %u, val_dut: %u\n",
        addr, v, v_dut);
    xrt_exit(1);
  }
}

static inline void mem_read_check32(uintptr_t addr, uint32_t v) {
  uint32_t v_dut = mem_read32(addr);
  if (v != v_dut) {
    printf(
        "mem_read_check32 failed, addr: %lx, val_expected: %u, val_dut: %u\n",
        addr, v, v_dut);
    xrt_exit(1);
  }
}

static inline void mem_read_check64(uintptr_t addr, uint64_t v) {
  uint64_t v_dut = mem_read64(addr);
  if (v != v_dut) {
    printf(
        "mem_read_check64 failed, addr: %lx, val_expected: %lu, val_dut: %lu\n",
        addr, v, v_dut);
    xrt_exit(1);
  }
}

static inline void mem_read_check128(uintptr_t addr, uint64_t v0, uint64_t v1) {
  mem_read_check64(addr, v0);
  mem_read_check64(addr + 8, v1);
}

static inline void mem_read_check256(uintptr_t addr, uint64_t v0, uint64_t v1,
                                     uint64_t v2, uint64_t v3) {
  mem_read_check128(addr, v0, v1);
  mem_read_check128(addr + 16, v2, v3);
}

static inline void mem_read_check512(uintptr_t addr, uint64_t v0, uint64_t v1,
                                     uint64_t v2, uint64_t v3, uint64_t v4,
                                     uint64_t v5, uint64_t v6, uint64_t v7) {
  mem_read_check256(addr, v0, v1, v2, v3);
  mem_read_check256(addr + 32, v4, v5, v6, v7);
}

static inline void init_cl(uintptr_t addr, uint64_t v0, uint64_t v1,
                           uint64_t v2, uint64_t v3, uint64_t v4, uint64_t v5,
                           uint64_t v6, uint64_t v7) {
  mem_write512(addr, v0, v1, v2, v3, v4, v5, v6, v7);
}

static inline void write_cl(uintptr_t addr, uint32_t offset, uint32_t size,
                            uint64_t v0, uint64_t v1, uint64_t v2, uint64_t v3,
                            uint64_t v4, uint64_t v5, uint64_t v6,
                            uint64_t v7) {
  switch (size) {
    case 1:
      switch (offset) {
        case (0):
          mem_write8(addr + offset, v0 >> (0));
          break;
        case (1):
          mem_write8(addr + offset, v0 >> (8));
          break;
        case (2):
          mem_write8(addr + offset, v0 >> (16));
          break;
        case (3):
          mem_write8(addr + offset, v0 >> (24));
          break;
        case (4):
          mem_write8(addr + offset, v0 >> (32));
          break;
        case (5):
          mem_write8(addr + offset, v0 >> (40));
          break;
        case (6):
          mem_write8(addr + offset, v0 >> (48));
          break;
        case (7):
          mem_write8(addr + offset, v0 >> (56));
          break;
        case (8):
          mem_write8(addr + offset, v1 >> (0));
          break;
        case (9):
          mem_write8(addr + offset, v1 >> (8));
          break;
        case (10):
          mem_write8(addr + offset, v1 >> (16));
          break;
        case (11):
          mem_write8(addr + offset, v1 >> (24));
          break;
        case (12):
          mem_write8(addr + offset, v1 >> (32));
          break;
        case (13):
          mem_write8(addr + offset, v1 >> (40));
          break;
        case (14):
          mem_write8(addr + offset, v1 >> (48));
          break;
        case (15):
          mem_write8(addr + offset, v1 >> (56));
          break;
        case (16):
          mem_write8(addr + offset, v2 >> (0));
          break;
        case (17):
          mem_write8(addr + offset, v2 >> (8));
          break;
        case (18):
          mem_write8(addr + offset, v2 >> (16));
          break;
        case (19):
          mem_write8(addr + offset, v2 >> (24));
          break;
        case (20):
          mem_write8(addr + offset, v2 >> (32));
          break;
        case (21):
          mem_write8(addr + offset, v2 >> (40));
          break;
        case (22):
          mem_write8(addr + offset, v2 >> (48));
          break;
        case (23):
          mem_write8(addr + offset, v2 >> (56));
          break;
        case (24):
          mem_write8(addr + offset, v3 >> (0));
          break;
        case (25):
          mem_write8(addr + offset, v3 >> (8));
          break;
        case (26):
          mem_write8(addr + offset, v3 >> (16));
          break;
        case (27):
          mem_write8(addr + offset, v3 >> (24));
          break;
        case (28):
          mem_write8(addr + offset, v3 >> (32));
          break;
        case (29):
          mem_write8(addr + offset, v3 >> (40));
          break;
        case (30):
          mem_write8(addr + offset, v3 >> (48));
          break;
        case (31):
          mem_write8(addr + offset, v3 >> (56));
          break;
        case (32):
          mem_write8(addr + offset, v4 >> (0));
          break;
        case (33):
          mem_write8(addr + offset, v4 >> (8));
          break;
        case (34):
          mem_write8(addr + offset, v4 >> (16));
          break;
        case (35):
          mem_write8(addr + offset, v4 >> (24));
          break;
        case (36):
          mem_write8(addr + offset, v4 >> (32));
          break;
        case (37):
          mem_write8(addr + offset, v4 >> (40));
          break;
        case (38):
          mem_write8(addr + offset, v4 >> (48));
          break;
        case (39):
          mem_write8(addr + offset, v4 >> (56));
          break;
        case (40):
          mem_write8(addr + offset, v5 >> (0));
          break;
        case (41):
          mem_write8(addr + offset, v5 >> (8));
          break;
        case (42):
          mem_write8(addr + offset, v5 >> (16));
          break;
        case (43):
          mem_write8(addr + offset, v5 >> (24));
          break;
        case (44):
          mem_write8(addr + offset, v5 >> (32));
          break;
        case (45):
          mem_write8(addr + offset, v5 >> (40));
          break;
        case (46):
          mem_write8(addr + offset, v5 >> (48));
          break;
        case (47):
          mem_write8(addr + offset, v5 >> (56));
          break;
        case (48):
          mem_write8(addr + offset, v6 >> (0));
          break;
        case (49):
          mem_write8(addr + offset, v6 >> (8));
          break;
        case (50):
          mem_write8(addr + offset, v6 >> (16));
          break;
        case (51):
          mem_write8(addr + offset, v6 >> (24));
          break;
        case (52):
          mem_write8(addr + offset, v6 >> (32));
          break;
        case (53):
          mem_write8(addr + offset, v6 >> (40));
          break;
        case (54):
          mem_write8(addr + offset, v6 >> (48));
          break;
        case (55):
          mem_write8(addr + offset, v6 >> (56));
          break;
        case (56):
          mem_write8(addr + offset, v7 >> (0));
          break;
        case (57):
          mem_write8(addr + offset, v7 >> (8));
          break;
        case (58):
          mem_write8(addr + offset, v7 >> (16));
          break;
        case (59):
          mem_write8(addr + offset, v7 >> (24));
          break;
        case (60):
          mem_write8(addr + offset, v7 >> (32));
          break;
        case (61):
          mem_write8(addr + offset, v7 >> (40));
          break;
        case (62):
          mem_write8(addr + offset, v7 >> (48));
          break;
        case (63):
          mem_write8(addr + offset, v7 >> (56));
          break;
        default:
          break;
      }
      break;
    case 2:
      switch (offset) {
        case (0):
          mem_write16(addr + offset, v0 >> (0));
          break;
        case (2):
          mem_write16(addr + offset, v0 >> (16));
          break;
        case (4):
          mem_write16(addr + offset, v0 >> (32));
          break;
        case (6):
          mem_write16(addr + offset, v0 >> (48));
          break;
        case (8):
          mem_write16(addr + offset, v1 >> (0));
          break;
        case (10):
          mem_write16(addr + offset, v1 >> (16));
          break;
        case (12):
          mem_write16(addr + offset, v1 >> (32));
          break;
        case (14):
          mem_write16(addr + offset, v1 >> (48));
          break;
        case (16):
          mem_write16(addr + offset, v2 >> (0));
          break;
        case (18):
          mem_write16(addr + offset, v2 >> (16));
          break;
        case (20):
          mem_write16(addr + offset, v2 >> (32));
          break;
        case (22):
          mem_write16(addr + offset, v2 >> (48));
          break;
        case (24):
          mem_write16(addr + offset, v3 >> (0));
          break;
        case (26):
          mem_write16(addr + offset, v3 >> (16));
          break;
        case (28):
          mem_write16(addr + offset, v3 >> (32));
          break;
        case (30):
          mem_write16(addr + offset, v3 >> (48));
          break;
        case (32):
          mem_write16(addr + offset, v4 >> (0));
          break;
        case (34):
          mem_write16(addr + offset, v4 >> (16));
          break;
        case (36):
          mem_write16(addr + offset, v4 >> (32));
          break;
        case (38):
          mem_write16(addr + offset, v4 >> (48));
          break;
        case (40):
          mem_write16(addr + offset, v5 >> (0));
          break;
        case (42):
          mem_write16(addr + offset, v5 >> (16));
          break;
        case (44):
          mem_write16(addr + offset, v5 >> (32));
          break;
        case (46):
          mem_write16(addr + offset, v5 >> (48));
          break;
        case (48):
          mem_write16(addr + offset, v6 >> (0));
          break;
        case (50):
          mem_write16(addr + offset, v6 >> (16));
          break;
        case (52):
          mem_write16(addr + offset, v6 >> (32));
          break;
        case (54):
          mem_write16(addr + offset, v6 >> (48));
          break;
        case (56):
          mem_write16(addr + offset, v7 >> (0));
          break;
        case (58):
          mem_write16(addr + offset, v7 >> (16));
          break;
        case (60):
          mem_write16(addr + offset, v7 >> (32));
          break;
        case (62):
          mem_write16(addr + offset, v7 >> (48));
          break;
        default:
          break;
      }
      break;
    case 4:
      switch (offset) {
        case (0):
          mem_write32(addr + offset, v0 >> (0));
          break;
        case (4):
          mem_write32(addr + offset, v0 >> (32));
          break;
        case (8):
          mem_write32(addr + offset, v1 >> (0));
          break;
        case (12):
          mem_write32(addr + offset, v1 >> (32));
          break;
        case (16):
          mem_write32(addr + offset, v2 >> (0));
          break;
        case (20):
          mem_write32(addr + offset, v2 >> (32));
          break;
        case (24):
          mem_write32(addr + offset, v3 >> (0));
          break;
        case (28):
          mem_write32(addr + offset, v3 >> (32));
          break;
        case (32):
          mem_write32(addr + offset, v4 >> (0));
          break;
        case (36):
          mem_write32(addr + offset, v4 >> (32));
          break;
        case (40):
          mem_write32(addr + offset, v5 >> (0));
          break;
        case (44):
          mem_write32(addr + offset, v5 >> (32));
          break;
        case (48):
          mem_write32(addr + offset, v6 >> (0));
          break;
        case (52):
          mem_write32(addr + offset, v6 >> (32));
          break;
        case (56):
          mem_write32(addr + offset, v7 >> (0));
          break;
        case (60):
          mem_write32(addr + offset, v7 >> (32));
          break;
        default:
          break;
      }
      break;
    case 8:
      switch (offset) {
        case (0):
          mem_write64(addr + offset, v0);
          break;
        case (8):
          mem_write64(addr + offset, v1);
          break;
        case (16):
          mem_write64(addr + offset, v2);
          break;
        case (24):
          mem_write64(addr + offset, v3);
          break;
        case (32):
          mem_write64(addr + offset, v4);
          break;
        case (40):
          mem_write64(addr + offset, v5);
          break;
        case (48):
          mem_write64(addr + offset, v6);
          break;
        case (56):
          mem_write64(addr + offset, v7);
          break;
        default:
          break;
      }
      break;
    case 16:
      switch (offset) {
        case (0):
          mem_write128(addr + offset, v0, v1);
          break;
        case (16):
          mem_write128(addr + offset, v2, v3);
          break;
        case (32):
          mem_write128(addr + offset, v4, v5);
          break;
        case (48):
          mem_write128(addr + offset, v6, v7);
          break;
        default:
          break;
      }
      break;
    case 32:
      switch (offset) {
        case (0):
          mem_write256(addr + offset, v0, v1, v2, v3);
          break;
        case (32):
          mem_write256(addr + offset, v4, v5, v6, v7);
          break;
        default:
          break;
      }
      break;
    case 64:
      switch (offset) {
        case (0):
          mem_write512(addr + offset, v0, v1, v2, v3, v4, v5, v6, v7);
          break;
        default:
          break;
      }
      break;
    default:
      break;
  }
}
static inline void read_check_cl(uintptr_t addr, uint32_t offset, uint32_t size,
                                 uint64_t v0, uint64_t v1, uint64_t v2,
                                 uint64_t v3, uint64_t v4, uint64_t v5,
                                 uint64_t v6, uint64_t v7) {
  switch (size) {
    case 1:
      switch (offset) {
        case (0):
          mem_read_check8(addr + offset, v0 >> (0));
          break;
        case (1):
          mem_read_check8(addr + offset, v0 >> (8));
          break;
        case (2):
          mem_read_check8(addr + offset, v0 >> (16));
          break;
        case (3):
          mem_read_check8(addr + offset, v0 >> (24));
          break;
        case (4):
          mem_read_check8(addr + offset, v0 >> (32));
          break;
        case (5):
          mem_read_check8(addr + offset, v0 >> (40));
          break;
        case (6):
          mem_read_check8(addr + offset, v0 >> (48));
          break;
        case (7):
          mem_read_check8(addr + offset, v0 >> (56));
          break;
        case (8):
          mem_read_check8(addr + offset, v1 >> (0));
          break;
        case (9):
          mem_read_check8(addr + offset, v1 >> (8));
          break;
        case (10):
          mem_read_check8(addr + offset, v1 >> (16));
          break;
        case (11):
          mem_read_check8(addr + offset, v1 >> (24));
          break;
        case (12):
          mem_read_check8(addr + offset, v1 >> (32));
          break;
        case (13):
          mem_read_check8(addr + offset, v1 >> (40));
          break;
        case (14):
          mem_read_check8(addr + offset, v1 >> (48));
          break;
        case (15):
          mem_read_check8(addr + offset, v1 >> (56));
          break;
        case (16):
          mem_read_check8(addr + offset, v2 >> (0));
          break;
        case (17):
          mem_read_check8(addr + offset, v2 >> (8));
          break;
        case (18):
          mem_read_check8(addr + offset, v2 >> (16));
          break;
        case (19):
          mem_read_check8(addr + offset, v2 >> (24));
          break;
        case (20):
          mem_read_check8(addr + offset, v2 >> (32));
          break;
        case (21):
          mem_read_check8(addr + offset, v2 >> (40));
          break;
        case (22):
          mem_read_check8(addr + offset, v2 >> (48));
          break;
        case (23):
          mem_read_check8(addr + offset, v2 >> (56));
          break;
        case (24):
          mem_read_check8(addr + offset, v3 >> (0));
          break;
        case (25):
          mem_read_check8(addr + offset, v3 >> (8));
          break;
        case (26):
          mem_read_check8(addr + offset, v3 >> (16));
          break;
        case (27):
          mem_read_check8(addr + offset, v3 >> (24));
          break;
        case (28):
          mem_read_check8(addr + offset, v3 >> (32));
          break;
        case (29):
          mem_read_check8(addr + offset, v3 >> (40));
          break;
        case (30):
          mem_read_check8(addr + offset, v3 >> (48));
          break;
        case (31):
          mem_read_check8(addr + offset, v3 >> (56));
          break;
        case (32):
          mem_read_check8(addr + offset, v4 >> (0));
          break;
        case (33):
          mem_read_check8(addr + offset, v4 >> (8));
          break;
        case (34):
          mem_read_check8(addr + offset, v4 >> (16));
          break;
        case (35):
          mem_read_check8(addr + offset, v4 >> (24));
          break;
        case (36):
          mem_read_check8(addr + offset, v4 >> (32));
          break;
        case (37):
          mem_read_check8(addr + offset, v4 >> (40));
          break;
        case (38):
          mem_read_check8(addr + offset, v4 >> (48));
          break;
        case (39):
          mem_read_check8(addr + offset, v4 >> (56));
          break;
        case (40):
          mem_read_check8(addr + offset, v5 >> (0));
          break;
        case (41):
          mem_read_check8(addr + offset, v5 >> (8));
          break;
        case (42):
          mem_read_check8(addr + offset, v5 >> (16));
          break;
        case (43):
          mem_read_check8(addr + offset, v5 >> (24));
          break;
        case (44):
          mem_read_check8(addr + offset, v5 >> (32));
          break;
        case (45):
          mem_read_check8(addr + offset, v5 >> (40));
          break;
        case (46):
          mem_read_check8(addr + offset, v5 >> (48));
          break;
        case (47):
          mem_read_check8(addr + offset, v5 >> (56));
          break;
        case (48):
          mem_read_check8(addr + offset, v6 >> (0));
          break;
        case (49):
          mem_read_check8(addr + offset, v6 >> (8));
          break;
        case (50):
          mem_read_check8(addr + offset, v6 >> (16));
          break;
        case (51):
          mem_read_check8(addr + offset, v6 >> (24));
          break;
        case (52):
          mem_read_check8(addr + offset, v6 >> (32));
          break;
        case (53):
          mem_read_check8(addr + offset, v6 >> (40));
          break;
        case (54):
          mem_read_check8(addr + offset, v6 >> (48));
          break;
        case (55):
          mem_read_check8(addr + offset, v6 >> (56));
          break;
        case (56):
          mem_read_check8(addr + offset, v7 >> (0));
          break;
        case (57):
          mem_read_check8(addr + offset, v7 >> (8));
          break;
        case (58):
          mem_read_check8(addr + offset, v7 >> (16));
          break;
        case (59):
          mem_read_check8(addr + offset, v7 >> (24));
          break;
        case (60):
          mem_read_check8(addr + offset, v7 >> (32));
          break;
        case (61):
          mem_read_check8(addr + offset, v7 >> (40));
          break;
        case (62):
          mem_read_check8(addr + offset, v7 >> (48));
          break;
        case (63):
          mem_read_check8(addr + offset, v7 >> (56));
          break;
        default:
          break;
      }
      break;
    case 2:
      switch (offset) {
        case (0):
          mem_read_check16(addr + offset, v0 >> (0));
          break;
        case (2):
          mem_read_check16(addr + offset, v0 >> (16));
          break;
        case (4):
          mem_read_check16(addr + offset, v0 >> (32));
          break;
        case (6):
          mem_read_check16(addr + offset, v0 >> (48));
          break;
        case (8):
          mem_read_check16(addr + offset, v1 >> (0));
          break;
        case (10):
          mem_read_check16(addr + offset, v1 >> (16));
          break;
        case (12):
          mem_read_check16(addr + offset, v1 >> (32));
          break;
        case (14):
          mem_read_check16(addr + offset, v1 >> (48));
          break;
        case (16):
          mem_read_check16(addr + offset, v2 >> (0));
          break;
        case (18):
          mem_read_check16(addr + offset, v2 >> (16));
          break;
        case (20):
          mem_read_check16(addr + offset, v2 >> (32));
          break;
        case (22):
          mem_read_check16(addr + offset, v2 >> (48));
          break;
        case (24):
          mem_read_check16(addr + offset, v3 >> (0));
          break;
        case (26):
          mem_read_check16(addr + offset, v3 >> (16));
          break;
        case (28):
          mem_read_check16(addr + offset, v3 >> (32));
          break;
        case (30):
          mem_read_check16(addr + offset, v3 >> (48));
          break;
        case (32):
          mem_read_check16(addr + offset, v4 >> (0));
          break;
        case (34):
          mem_read_check16(addr + offset, v4 >> (16));
          break;
        case (36):
          mem_read_check16(addr + offset, v4 >> (32));
          break;
        case (38):
          mem_read_check16(addr + offset, v4 >> (48));
          break;
        case (40):
          mem_read_check16(addr + offset, v5 >> (0));
          break;
        case (42):
          mem_read_check16(addr + offset, v5 >> (16));
          break;
        case (44):
          mem_read_check16(addr + offset, v5 >> (32));
          break;
        case (46):
          mem_read_check16(addr + offset, v5 >> (48));
          break;
        case (48):
          mem_read_check16(addr + offset, v6 >> (0));
          break;
        case (50):
          mem_read_check16(addr + offset, v6 >> (16));
          break;
        case (52):
          mem_read_check16(addr + offset, v6 >> (32));
          break;
        case (54):
          mem_read_check16(addr + offset, v6 >> (48));
          break;
        case (56):
          mem_read_check16(addr + offset, v7 >> (0));
          break;
        case (58):
          mem_read_check16(addr + offset, v7 >> (16));
          break;
        case (60):
          mem_read_check16(addr + offset, v7 >> (32));
          break;
        case (62):
          mem_read_check16(addr + offset, v7 >> (48));
          break;
        default:
          break;
      }
      break;
    case 4:
      switch (offset) {
        case (0):
          mem_read_check32(addr + offset, v0 >> (0));
          break;
        case (4):
          mem_read_check32(addr + offset, v0 >> (32));
          break;
        case (8):
          mem_read_check32(addr + offset, v1 >> (0));
          break;
        case (12):
          mem_read_check32(addr + offset, v1 >> (32));
          break;
        case (16):
          mem_read_check32(addr + offset, v2 >> (0));
          break;
        case (20):
          mem_read_check32(addr + offset, v2 >> (32));
          break;
        case (24):
          mem_read_check32(addr + offset, v3 >> (0));
          break;
        case (28):
          mem_read_check32(addr + offset, v3 >> (32));
          break;
        case (32):
          mem_read_check32(addr + offset, v4 >> (0));
          break;
        case (36):
          mem_read_check32(addr + offset, v4 >> (32));
          break;
        case (40):
          mem_read_check32(addr + offset, v5 >> (0));
          break;
        case (44):
          mem_read_check32(addr + offset, v5 >> (32));
          break;
        case (48):
          mem_read_check32(addr + offset, v6 >> (0));
          break;
        case (52):
          mem_read_check32(addr + offset, v6 >> (32));
          break;
        case (56):
          mem_read_check32(addr + offset, v7 >> (0));
          break;
        case (60):
          mem_read_check32(addr + offset, v7 >> (32));
          break;
        default:
          break;
      }
      break;
    case 8:
      switch (offset) {
        case (0):
          mem_read_check64(addr + offset, v0);
          break;
        case (8):
          mem_read_check64(addr + offset, v1);
          break;
        case (16):
          mem_read_check64(addr + offset, v2);
          break;
        case (24):
          mem_read_check64(addr + offset, v3);
          break;
        case (32):
          mem_read_check64(addr + offset, v4);
          break;
        case (40):
          mem_read_check64(addr + offset, v5);
          break;
        case (48):
          mem_read_check64(addr + offset, v6);
          break;
        case (56):
          mem_read_check64(addr + offset, v7);
          break;
        default:
          break;
      }
      break;
    case 16:
      switch (offset) {
        case (0):
          mem_read_check128(addr + offset, v0, v1);
          break;
        case (16):
          mem_read_check128(addr + offset, v2, v3);
          break;
        case (32):
          mem_read_check128(addr + offset, v4, v5);
          break;
        case (48):
          mem_read_check128(addr + offset, v6, v7);
          break;
        default:
          break;
      }
      break;
    case 32:
      switch (offset) {
        case (0):
          mem_read_check256(addr + offset, v0, v1, v2, v3);
          break;
        case (32):
          mem_read_check256(addr + offset, v4, v5, v6, v7);
          break;
        default:
          break;
      }
      break;
    case 64:
      switch (offset) {
        case (0):
          mem_read_check512(addr + offset, v0, v1, v2, v3, v4, v5, v6, v7);
          break;
        default:
          break;
      }
      break;
    default:
      break;
  }
}

// cache maintainance
// 总是整 cacheline 操作
static inline void dc_cl(uintptr_t addr) {}

static inline void dma_write_cl(uintptr_t addr, uint64_t v0, uint64_t v1,
                                uint64_t v2, uint64_t v3, uint64_t v4,
                                uint64_t v5, uint64_t v6, uint64_t v7) {
  write_cl(addr, 0, 64, v0, v1, v2, v3, v4, v5, v6, v7);
}

static inline void dma_read_check_cl(uintptr_t addr, uint64_t v0, uint64_t v1,
                                     uint64_t v2, uint64_t v3, uint64_t v4,
                                     uint64_t v5, uint64_t v6, uint64_t v7) {
  read_check_cl(addr, 0, 64, v0, v1, v2, v3, v4, v5, v6, v7);
}
