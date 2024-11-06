#include <stdint.h>

#include "adler32.h"

typedef struct pattern_data {
  uint32_t *data;
  size_t mask;
} pattern_data_t;

#include "pattern.h"

void fill(void *addr, size_t page_length, int pattern_idx, size_t bus_shift,
          int inverse) {
  uint64_t *memwords = (uint64_t *)addr;
  pattern_data_t pattern_data = pattern_data_array[pattern_idx];

  for (size_t i = 0; i < page_length / sizeof(uint64_t); i++) {
    datacast_t data;
    size_t offset_l = i << 1;
    size_t offset_h = (i << 1) + 1;
    uint32_t ld;
    uint32_t hd;
    offset_l = (offset_l >> bus_shift);
    offset_h = (offset_h >> bus_shift);

    ld = pattern_data.data[offset_l & pattern_data.mask];
    hd = pattern_data.data[offset_h & pattern_data.mask];

    if (inverse) {
      ld = ~ld;
      hd = ~hd;
    }

    data.l32.l = ld;
    data.l32.h = hd;

    memwords[i] = data.l64;
  }
}