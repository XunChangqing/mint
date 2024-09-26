// author : zuoqian
// Copyright 2024. All rights reserved.

#pragma once

#include <stdint.h>
#include <stdlib.h>

typedef struct adler_checksum{
  uint64_t a1;
  uint64_t a2;
  uint64_t b1;
  uint64_t b2;
} adler_checksum_t;

static int checksum_equal(adler_checksum_t *l, adler_checksum_t *r) {
  if (l->a1 == r->a1 && l->a2 == r->a2 && l->b1 == r->b1 && r->b2 == r->b2) {
    return -1;
  }
  return 0;
}

typedef union datacast {
  uint64_t l64;
  struct {
    uint32_t l;
    uint32_t h;
  } l32;
} datacast_t;

// Calculates Adler checksum for supplied data.
void cacl_adler_checksum(uint64_t *data64, size_t size_in_bytes,
                         adler_checksum_t *checksum);
