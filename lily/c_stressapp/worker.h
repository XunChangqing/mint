#pragma once

// #include <stdlib.h>
// #include <stdbool.h>
#include "adler32.h"

void fill(void *addr, size_t page_length, size_t pattern_idx, size_t bus_shift,
          int inverse);

void copy(void *src, void *dst, size_t page_length);

void invert_up(void *buf, size_t page_length);
void invert_down(void *buf, size_t page_length);
static void invert(void *buf, size_t page_length) {
  invert_down(buf, page_length);
  invert_up(buf, page_length);
}

void check(void *buf, size_t page_length, adler_checksum_t checksum);
