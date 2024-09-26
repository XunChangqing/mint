#include "worker.h"

#include "xrt.h"
#include "print.h"

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
