#pragma once
// 1. 自身只支持从ddr加载
// 2. kernel也必须是后门加载
// 3. 从核只支持spin-table方式唤醒
// 目前仅用于软仿，存控、DCU等都通过sv初始化

///////////////////////////////////////////////////////////
// 需要修改
// tiny loader自身的加载地址，一般为ddr最小的地址
#define LOAD_ADDR (0x40000000)
// kernel的入口地址
#define KERNEL_ENTRY_ADDR (0x40080000)
// 处理核数量
#define NR_CPUS (1)
///////////////////////////////////////////////////////////

#define ID_AA64PFR0_EL2_SHIFT 8
// 下一级使用aarch64模式
#define HCR_RW (1 << 31)
// TGE使得EL0的异常直接陷入到EL2，也是VHE支持的一部分
#define HCR_TGE (1 << 27)
// 允许host（例如带kvm支持的linux）直接运行在EL2，而不是EL1，并且在EL2还可以很
// 简便的与EL0交互，这是VHE的一部分，比如访问一些寄存器的EL2名字时直接访问的是EL1
// 的寄存器
#define HCR_E2H (1 << 34)
// 下一级使用aarch64模式
#define SCR_RW (1 << 10)
// 允许hvc调用
#define SCR_HCE (1 << 8)
// 非安全
#define SCR_NS (1 << 0)
/*
 * PSR bits
 */
#define PSR_MODE_EL0t 0x00000000
#define PSR_MODE_EL1t 0x00000004
#define PSR_MODE_EL1h 0x00000005
#define PSR_MODE_EL2t 0x00000008
#define PSR_MODE_EL2h 0x00000009
#define PSR_MODE_EL3t 0x0000000c
#define PSR_MODE_EL3h 0x0000000d
#define PSR_MODE_MASK 0x0000000f

/* AArch64 SPSR bits */
#define PSR_F_BIT 0x00000040
#define PSR_I_BIT 0x00000080
#define PSR_A_BIT 0x00000100
#define PSR_D_BIT 0x00000200
#define PSR_PAN_BIT 0x00400000
#define PSR_UAO_BIT 0x00800000
#define PSR_V_BIT 0x10000000
#define PSR_C_BIT 0x20000000
#define PSR_Z_BIT 0x40000000
#define PSR_N_BIT 0x80000000

/* Current Exception Level values, as contained in CurrentEL */
#define CurrentEL_EL1 (1 << 2)
#define CurrentEL_EL2 (2 << 2)
#define CurrentEL_EL3 (3 << 2)
