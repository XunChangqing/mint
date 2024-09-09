#include "config.h"

    .section    ".head.text","ax"
_head:
    b _entry

    .align 4
    .section    ".text","ax"
    // 此处需要根据处理核数量修改, release address 从10开始
_release_addr:
    .quad   0
_mpidr_data:
    .quad   0x80000000

_entry:
    // 所有核降低el级别到el1
    bl _el3_setup
    bl _el2_setup

    // logic core id in x4
    mrs x11, mpidr_el1
    mov x4, 0
    adr x5, _mpidr_data
_logic_id_loop:
    ldr x6, [x5]
    cmp x11, x6
    beq _found
    add x5, x5, 8
    add x4, x4, 8
    cmp x4, #NR_CPUS
    blt _logic_id_loop
_error_sleep:
    wfe
    b _error_sleep

_found:
    // 主核跳转到kernel入口
    cmp x4, 0
    bne _secondary_cpus
    // x0 - x3 清零
    mov x0, 0
    mov x1, 0
    mov x2, 0
    mov x3, 0
    ldr x10, =KERNEL_ENTRY_ADDR
    br x10

    // 从核spin release addr
_secondary_cpus:
    adr x5, _release_addr
    add x5, x5, x4
_spin_loop:
    ldr x6, [x5]
    cmp x6, 0
    beq _spin_loop
    // x0 - x3 清零
    mov x0, 0
    mov x1, 0
    mov x2, 0
    mov x3, 0
    br x6

_el3_setup:
	mrs	x0, CurrentEL
	cmp	x0, #CurrentEL_EL3
	b.eq	1f
	isb
	ret

    // 下降EL级别之前，需要配置允许串口等地址在NS下访问的权限
1:	mov x0, #(SCR_RW | SCR_HCE | SCR_NS)
    msr scr_el3, x0
    /* spsr */
	mov	x0, #(PSR_F_BIT | PSR_I_BIT | PSR_A_BIT | PSR_D_BIT | PSR_MODE_EL2h)

    // 检查el2是否存在，如果存在下降到EL2，否则下降到EL1
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