# author: zuoqian
# Copyright 2023. All rights reserved.

// 启动要求
// MMU关闭，D-cache关闭，I-cache关闭, EL=1，所有核都必须进入入口点
// x0 = physical address to the FDT blob.，
// 如果不输入fdt，则x0需要置0，否则运行时会访问该地址检查dt的关键内容是否一致

#include <ivy/halt_code.h>
#include "ivy_pt.h"
#include "ivy_dt.h"
#include "ivy_cfg.h"
#include "sysreg.h"

	.macro	le64sym, sym
	.long	\sym\()_lo32
	.long	\sym\()_hi32
	.endm

	/*
 * Pseudo-ops for PC-relative adr/ldr/str <reg>, <symbol> where
 * <symbol> is within the range +/- 4 GB of the PC.
 */
	/*
	 * @dst: destination register (64 bit wide)
	 * @sym: name of the symbol
	 */
	.macro	adr_l, dst, sym
	adrp	\dst, \sym
	add	\dst, \dst, :lo12:\sym
	.endm

	/*
	 * @dst: destination register (32 or 64 bit wide)
	 * @sym: name of the symbol
	 * @tmp: optional 64-bit scratch register to be used if <dst> is a
	 *       32-bit wide register, in which case it cannot be used to hold
	 *       the address
	 */
	.macro	ldr_l, dst, sym, tmp=
	.ifb	\tmp
	adrp	\dst, \sym
	ldr	\dst, [\dst, :lo12:\sym]
	.else
	adrp	\tmp, \sym
	ldr	\dst, [\tmp, :lo12:\sym]
	.endif
	.endm

	/*
	 * @src: source register (32 or 64 bit wide)
	 * @sym: name of the symbol
	 * @tmp: mandatory 64-bit scratch register to calculate the address
	 *       while <src> needs to be preserved.
	 */
	.macro	str_l, src, sym, tmp
	adrp	\tmp, \sym
	str	\src, [\tmp, :lo12:\sym]
	.endm

	/*
	 * @dst: Result of per_cpu(sym, smp_processor_id()) (can be SP)
	 * @sym: The name of the per-cpu variable
	 * @tmp: scratch register
	 */
	.macro adr_this_cpu, dst, sym, tmp
	adrp	\tmp, \sym
	add	\dst, \tmp, #:lo12:\sym
alternative_if_not ARM64_HAS_VIRT_HOST_EXTN
	mrs	\tmp, tpidr_el1
alternative_else
	mrs	\tmp, tpidr_el2
alternative_endif
	add	\dst, \dst, \tmp
	.endm

	.section    ".head.text","ax"
	.global _head
_head:
#ifndef IVY_CFG_NO_BOOTER
	// 注意该头部是对linux内核头部的规范，不是uboot image文件的规范
//#ifdef CONFIG_EFI
//	/*
//	 * This add instruction has no meaningful effect except that
//	 * its opcode forms the magic "MZ" signature required by UEFI.
//	 */
//	add	x13, x18, #0x16
//	b	_cpu_setup
//#else
	b _primary_entry			// branch to kernel start, magic
	.long	0				// reserved
//#endif
	le64sym	_kernel_offset_le		// Image load offset from start of RAM, little-endian
	le64sym	_kernel_size_le			// Effective size of kernel image, little-endian
	le64sym	_kernel_flags_le		// Informative flags, little-endian
	.quad	0				// reserved
	.quad	0				// reserved
	.quad	0				// reserved
	.ascii	"ARM\x64"			// Magic number
//#ifdef CONFIG_EFI
//	.long	pe_header - _head		// Offset to the PE header.
//
//pe_header:
//	__EFI_PE_HEADER
//#else
	.long	0				// reserved
//#endif
#else
	// 没有loader，要求所有核都进入入口
	msr	spsel, #1			// We want to use SP_EL{1,2}
	// 所有核先降级到el1
	bl _el3_setup
	bl _el2_setup
	bl _set_logic_core_id
	mov x0, 0
	cmp x20, 0
	beq _primary_entry
	adr x5, release_no_booter
_spin_loop:
	ldr x6, [x5]
	cmp x6, 0
	beq _spin_loop
	b _secondary_entry
#endif

	.section    ".text","ax"
_primary_entry:
	// fdt存到全局变量，在el发生可能的下降之前
	//adr x1, fdt_pointer
	//str x0, [x1]
	str_l x0, fdt_pointer, x1
    // 各个el级别使用各自sp寄存器，具体参见文档中关于sp访问说明
	msr	spsel, #1			// We want to use SP_EL{1,2}
	// 如果el3级别进入，则直接降级为el2
	bl _el3_setup
	bl _el2_setup
	bl _enable_mmu
	bl _set_logic_core_id
	bl _set_stack

	// 只支持在el1运行激励程序
	mov x29, 0
	mov x30, 0
	b primary_main

	/*
	 * spin-table
	 * This provides a "holding pen" for platforms to hold all secondary
	 * cores are held until we're ready for them to initialise.
	 */
//_secondary_holding_pen:
//	bl _el3_setup
//	bl _el2_setup			// Drop to EL1, w0=cpu_boot_mode
//	mrs	x0, mpidr_el1
//	mov_q	x1, MPIDR_HWID_BITMASK
//	and	x0, x0, x1
//	adr_l	x3, secondary_holding_pen_release
//_pen:
//	ldr	x4, [x3]
//	cmp	x4, x0
//	b.eq _secondary_startup
//	wfe
//	b _pen

	/*
	 * psci
	 * Secondary entry point that jumps straight into the kernel. Only to
	 * be used where CPUs are brought online dynamically by the kernel.
	 */
.global _secondary_entry
_secondary_entry:
	bl _el3_setup
	bl _el2_setup			// Drop to EL1
	bl _enable_mmu
	bl _set_logic_core_id
	bl _set_stack

	mov	x29, #0
	mov	x30, #0
	b	secondary_main

_el3_setup:
	mrs	x0, CurrentEL
	cmp	x0, #CurrentEL_EL3
	b.eq	1f
	isb
	ret

1:	mov x0, #(SCR_RW | SCR_HCE | SCR_NS)
    msr scr_el3, x0
    /* spsr */
	mov	x0, #(PSR_F_BIT | PSR_I_BIT | PSR_A_BIT | PSR_D_BIT | PSR_MODE_EL2h)

	// 检查el2是否存在
	mrs	x7, ID_AA64PFR0_EL1
	// el2 3个bit
	ubfx x7, x7, #ID_AA64PFR0_EL2_SHIFT, #3
	cbnz x7, 2f
	mov x0, #(PSR_F_BIT | PSR_I_BIT | PSR_A_BIT | PSR_D_BIT | PSR_MODE_EL1h)

2:	msr	spsr_el3, x0
    // 使用函数返回地址作为elr，直接eret即以el2级别返回
	msr	elr_el3, lr
	eret

_el2_setup:
	mrs	x0, CurrentEL
	cmp	x0, #CurrentEL_EL2
	b.eq	1f
	// mov_q	x0, (SCTLR_EL1_RES1 | ENDIAN_SET_EL1)
	// msr	sctlr_el1, x0
	// mov	w0, #BOOT_CPU_MODE_EL1		// This cpu booted in EL1
	isb
	ret

1:	//mov_q	x0, (SCTLR_EL2_RES1 | ENDIAN_SET_EL2)
	//msr	sctlr_el2, x0
    // 不使用VHE，运行EL1

//#ifdef CONFIG_ARM64_VHE
	/*
	 * Check for VHE being present. For the rest of the EL2 setup,
	 * x2 being non-zero indicates that we do have VHE, and that the
	 * kernel is intended to run at EL2.
	 */
//	mrs	x2, id_aa64mmfr1_el1
//	ubfx	x2, x2, #8, #4
//#else
	mov	x2, xzr
//#endif

	/* Hyp configuration. */
	mov	x0, #HCR_RW			// 64-bit EL1
	//cbz	x2, _set_hcr
    // TGE和E2H都不使能
	//orr	x0, x0, #HCR_TGE		// Enable Host Extensions
	//orr	x0, x0, #HCR_E2H
_set_hcr:
	msr	hcr_el2, x0
	isb

	/*
	 * Allow Non-secure EL1 and EL0 to access physical timer and counter.
	 * This is not necessary for VHE, since the host kernel runs in EL2,
	 * and EL0 accesses are configured in the later stage of boot process.
	 * Note that when HCR_EL2.E2H == 1, CNTHCTL_EL2 has the same bit layout
	 * as CNTKCTL_EL1, and CNTKCTL_EL1 accessing instructions are redefined
	 * to access CNTHCTL_EL2. This allows the kernel designed to run at EL1
	 * to transparently mess with the EL0 bits via CNTKCTL_EL1 access in
	 * EL2.
	 */
	//cbnz	x2, 1f
	mrs	x0, cnthctl_el2
	orr	x0, x0, #3			// Enable EL1 physical timers
	msr	cnthctl_el2, x0
1:
	msr	cntvoff_el2, xzr		// Clear virtual offset

	/* Populate ID registers. */
	mrs	x0, midr_el1
	mrs	x1, mpidr_el1
	msr	vpidr_el2, x0
	msr	vmpidr_el2, x1

	/* Stage-2 translation */
	msr	vttbr_el2, xzr

	//cbz	x2, install_el2_stub
	//mov	w0, #BOOT_CPU_MODE_EL2		// This CPU booted in EL2
	//isb
	//ret

	/* spsr */
	mov	x0, #(PSR_F_BIT | PSR_I_BIT | PSR_A_BIT | PSR_D_BIT | PSR_MODE_EL1h)
	msr	spsr_el2, x0
    // 使用函数返回地址作为elr，直接eret即以el1级别返回
	msr	elr_el2, lr
	// mov	w0, #BOOT_CPU_MODE_EL2		// This CPU booted in EL2
	eret
    
_enable_mmu:
 	tlbi vmalle1				// Invalidate local TLB
 	dsb	nsh

 	mov	x0, #3 << 20
 	msr	cpacr_el1, x0			// Enable FP/ASIMD
 	mov	x0, #1 << 12			// Reset mdscr_el1 and disable
 	msr	mdscr_el1, x0			// access to the DCC from EL0
 	isb					// Unmask debug exceptions now,

	// mair寄存器值来自脚本生成，因为页表也是来自脚本生成，页表属性要求保持一致
	ldr	x1, =MAIR_EL1_VAL
	msr	mair_el1, x1

	// TCR配置内容的3个重要部分
	// 两个页表的粒度，通过TG0, TG1(translation granuale)，由脚本根据激励配置生成
	// 两个页表的虚拟地址位宽，通过T0SZ, T1SZ，由基本根据激励配置生成
	// 页表输出物理地址位宽，通过访问硬件配置来设置
	// 加载TCR基本配置，包括前两个部分
	ldr	x1, =TCR_EL1_VAL
	// 根据硬件支持的物理地址位宽设置输出地址位宽，目前脚本输出的页表
	// 内容最大只能支持48位物理地址，所有这里控制不要超过
	mrs	x7, ID_AA64MMFR0_EL1
	// PARagne有4位，只保留低3位，与TCR中IPS位宽保持相同
	ubfx x7, x7, #ID_AA64MMFR0_PARANGE_SHIFT, #3
	mov	x8, #ID_AA64MMFR0_PARANGE_MAX
	cmp	x7, x8
	// 确保配置ips不会大于最大物理位宽
	csel x7, x8, x7, hi
	bfi	x1, x7, #TCR_IPS_SHIFT, #3
	// 设置tcr
	msr	tcr_el1, x1

	// 检查硬件是否支持当前所使用的页表粒度
	mrs x1, ID_AA64MMFR0_EL1
	ubfx x7, x1, #ID_AA64MMFR0_TGRAN_SHIFT, 4
	cmp	x7, #ID_AA64MMFR0_TGRAN_SUPPORTED
	// 硬件不支持，跳转到错误
	mov x0, #HALT_CODE_PT_GRAN_UNSUPPORTED
	b.ne _error_halt

	// 使用ttbr0进行默认线性映射
	ldr	x1, =PGD0
	msr	ttbr0_el1, x1
	// ttbr1用于用户自定义映射
	ldr	x1, =USER_PGD0
	msr	ttbr1_el1, x1
	isb

	ldr x1, =SCTLR_EL1_VAL
	msr	sctlr_el1, x1

	isb
	/*
	 * Invalidate the local I-cache so that any instructions fetched
	 * speculatively from the PoC are discarded, since they may have
	 * been dynamically patched at the PoU.
	 */
	ic	iallu
	dsb	nsh
	isb

	ret

_set_logic_core_id:
	adr_l x0, ivy_dt_cpu_id_map
	mrs x2, mpidr_el1
	ldr x3, =MPIDR_HWID_BITMASK
	and x2, x2, x3
	mov x20, 0
_logic_id_loop:
	ldr x1, [x0]
	cmp x1, x2
	beq _found
	add x0, x0, #0x8
	add	x20, x20, #0x1
	cmp	x20, #IVY_DT_NR_CPUS
	blt _logic_id_loop
	mov x0, #HALT_CODE_ILLEGAL_MPIDR
	b _error_halt

_found:
	// x20作为core id存到tpidr_el1，后续读取该寄存器可以获取core id
	msr tpidr_el1, x20
	ret

_set_stack:
	// 所有活跃处理核初始化堆栈地址
	ldr x0, =core_stack_start
	// 基地址乘以尺寸，得到每个处理核的基地址
	mov x2, #IVY_CFG_CORE_STACK_SIZE
	// tpidr_el1 + 1 作为偏移
	mrs x20, tpidr_el1
	add x20, x20, 1
	mul x3, x2, x20
	add x0, x0, x3
	// 初始化当前core的栈指针
	mov sp, x0
	ret

	.global _halt
	.global _error_halt
// 使用不同halt，方便根据pc判断
_halt:
	wfe
	b _halt

_error_halt:
	wfe
	b _error_halt
