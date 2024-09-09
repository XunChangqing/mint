#include "ivy_dt.h"
#include "ivy_cfg.h"
#include "image.h"

ENTRY(_head)

#define HEAD_TEXT  KEEP(*(.head.text))

SECTIONS
{
	. = IVY_CFG_TEXT_BASE;

	.head.text : {
        text_start = .;
        HEAD_TEXT
	}
	.text : {
        *(.text)
	}
    .rodata : {
        *(.rodata*)
    }
    . = ALIGN(8);
    .data : {
        *(.data*)
    }
    . = ALIGN(8);
    .bss : {
        *(.bss*)
    }
    . = ALIGN(IVY_CFG_PAGE_SIZE);
    .pt_data : {
        *(.pt_data)
    }
	// 处理核栈空间，页对齐
	. = ALIGN(IVY_CFG_PAGE_SIZE);
	core_stack_start = .;
    . += (IVY_CFG_CORE_STACK_SIZE*IVY_DT_NR_CPUS);
    text_end = .;

    HEAD_SYMBOLS

    /DISCARD/ : {
    *(.discard)
    *(.discard.*)
    *(.interp .dynamic)
    *(.dynsym .dynstr .hash .gnu.hash)
    *(.eh_frame)
    *(.comment)
    *(.note.*)
    *(.iplt)
    *(.rela.*)
    *(.got)
    *(.got.*)
    *(.igot)
    *(.igot.*)
	}
}
