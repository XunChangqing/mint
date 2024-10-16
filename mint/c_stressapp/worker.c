#include "worker.h"

#include <ivy/print.h>
#include <ivy/xrt.h>

void check(void *buf, size_t page_length, adler_checksum_t checksum) {
  const int blocksize = 4096;
  const int blockwords = blocksize / sizeof(uint64_t);
  int blocks = page_length / blocksize;

  uint64_t *memblock = (uint64_t *)buf;

  for (int cur_block = 0; cur_block < blocks; cur_block++) {
    uint64_t *memslice = memblock + cur_block * blockwords;
    adler_checksum_t crc;
    cacl_adler_checksum(memslice, blocksize, &crc);

    if (!checksum_equal(&crc, &checksum)) {
      printf("error\n");
      xrt_exit(1);
    }
  }
}

void copy(void *src, void *dst, size_t page_length) {
  memcpy(dst, src, page_length);
}

void invert_up(void *buf, size_t page_length) {
  const int blocksize = 4096;
  const int blockwords = blocksize / sizeof(uint64_t);
  unsigned int blocks = page_length / blocksize;

  uint64_t *iter = (uint64_t *)buf;
  uint64_t *end = (uint64_t *)buf + blocks * blockwords;

  while (iter != end) {
    *iter = ~(*iter);
    iter++;
  }
}

void invert_down(void *buf, size_t page_length) {
  const int blocksize = 4096;
  const int blockwords = blocksize / sizeof(uint64_t);
  unsigned int blocks = page_length / blocksize;

  uint64_t *iter = (uint64_t *)buf + blocks * blockwords;
  uint64_t *rend = (uint64_t *)buf;

  while (iter != rend) {
    iter--;
    *iter = ~(*iter);
  }
}
