#include "config.h"

OUTPUT_FORMAT("elf64-littleaarch64", "elf64-littleaarch64", "elf64-littleaarch64")
OUTPUT_ARCH(aarch64)

#define HEAD_TEXT KEEP(*(.head.text))

SECTIONS
{
  . = LOAD_ADDR;
  .head.text : {
      HEAD_TEXT
  }
  .text : {
      *(.text)
  }
  .data : {
    *(.data)
  }
  .rodata : {
    *(.rodata)
  }
  .rela.dyn : {
    *(.rela*)
  }
  .bss : {
    *(.bss)
  }
  /DISCARD/ : { *(.eh_frame) }
}
