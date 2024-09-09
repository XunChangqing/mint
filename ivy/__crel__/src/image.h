#pragma once
// 来自linux，只在linker script中包含

#ifdef CONFIG_CPU_BIG_ENDIAN
#define DATA_LE32(data)                                       \
  ((((data)&0x000000ff) << 24) | (((data)&0x0000ff00) << 8) | \
   (((data)&0x00ff0000) >> 8) | (((data)&0xff000000) >> 24))
#else
#define DATA_LE32(data) ((data)&0xffffffff)
#endif

#define DEFINE_IMAGE_LE64(sym, data)         \
  sym##_lo32 = DATA_LE32((data)&0xffffffff); \
  sym##_hi32 = DATA_LE32((data) >> 32)

#define DEFINE_IMAGE_LE64(sym, data)         \
  sym##_lo32 = DATA_LE32((data)&0xffffffff); \
  sym##_hi32 = DATA_LE32((data) >> 32)

#ifdef CONFIG_CPU_BIG_ENDIAN
#define __HEAD_FLAG_BE 1
#else
#define __HEAD_FLAG_BE 0
#endif

#define __HEAD_FLAG_PAGE_SIZE ((IVY_CFG_PAGE_SHIFT - 10) / 2)

#define __HEAD_FLAG_PHYS_BASE 1

#define __HEAD_FLAGS                                      \
  ((__HEAD_FLAG_BE << 0) | (__HEAD_FLAG_PAGE_SIZE << 1) | \
   (__HEAD_FLAG_PHYS_BASE << 3))

/*
 * These will output as part of the Image header, which should be little-endian
 * regardless of the endianness of the kernel. While constant values could be
 * endian swapped in head.S, all are done here for consistency.
 */
#define HEAD_SYMBOLS                                         \
  DEFINE_IMAGE_LE64(_kernel_size_le, text_end - text_start); \
  DEFINE_IMAGE_LE64(_kernel_offset_le, IVY_CFG_TEXT_OFFSET); \
  DEFINE_IMAGE_LE64(_kernel_flags_le, __HEAD_FLAGS);
