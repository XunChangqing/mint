#include "adler32.h"

void cacl_adler_checksum(uint64_t *data64, size_t size_in_bytes,
                         adler_checksum_t *checksum) {
  // Use this data wrapper to access memory with 64bit read/write.
  datacast_t data;
  size_t count = size_in_bytes / sizeof(data);

//   if (count > (1U) << 19) {
    // Size is too large, must be strictly less than 512 KB.
//     return false;
//   }

  uint64_t a1 = 1;
  uint64_t a2 = 1;
  uint64_t b1 = 0;
  uint64_t b2 = 0;

  size_t i = 0;
  while (i < count) {
    // Process 64 bits at a time.
    data.l64 = data64[i];
    a1 = a1 + data.l32.l;
    b1 = b1 + a1;
    a1 = a1 + data.l32.h;
    b1 = b1 + a1;
    i++;

    data.l64 = data64[i];
    a2 = a2 + data.l32.l;
    b2 = b2 + a2;
    a2 = a2 + data.l32.h;
    b2 = b2 + a2;
    i++;
  }
  checksum->a1 = a1;
  checksum->a2 = a2;
  checksum->b1 = b1;
  checksum->b2 = b2;
}
