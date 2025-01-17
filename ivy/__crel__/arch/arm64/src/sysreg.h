// Copyright 2024 zuoqian, zuoqian@qq.com

#pragma once
#include "ivy_cfg.h"
#include "ivy_dt.h"

#define INVALID_HWID ULONG_MAX

#define MPIDR_UP_BITMASK (0x1 << 30)
#define MPIDR_MT_BITMASK (0x1 << 24)
#define MPIDR_HWID_BITMASK 0xff00fffffful

/* id_aa64mmfr0 */
#define ID_AA64MMFR0_BIGENDEL0_SHIFT 16
#define ID_AA64MMFR0_SNSMEM_SHIFT 12
#define ID_AA64MMFR0_BIGENDEL_SHIFT 8
#define ID_AA64MMFR0_ASID_SHIFT 4
#define ID_AA64MMFR0_PARANGE_SHIFT 0

#define ID_AA64MMFR0_TGRAN4_SHIFT 28
#define ID_AA64MMFR0_TGRAN64_SHIFT 24
#define ID_AA64MMFR0_TGRAN16_SHIFT 20

#define ID_AA64MMFR0_TGRAN4_NI 0xf
#define ID_AA64MMFR0_TGRAN4_SUPPORTED 0x0
#define ID_AA64MMFR0_TGRAN64_NI 0xf
#define ID_AA64MMFR0_TGRAN64_SUPPORTED 0x0
#define ID_AA64MMFR0_TGRAN16_NI 0x0
#define ID_AA64MMFR0_TGRAN16_SUPPORTED 0x1
#define ID_AA64MMFR0_PARANGE_48 0x5
#define ID_AA64MMFR0_PARANGE_52 0x6

#if defined(IVY_CFG_ARM64_4K_PAGES)
#define ID_AA64MMFR0_TGRAN_SHIFT ID_AA64MMFR0_TGRAN4_SHIFT
#define ID_AA64MMFR0_TGRAN_SUPPORTED ID_AA64MMFR0_TGRAN4_SUPPORTED
#elif defined(IVY_CFG_ARM64_16K_PAGES)
#define ID_AA64MMFR0_TGRAN_SHIFT ID_AA64MMFR0_TGRAN16_SHIFT
#define ID_AA64MMFR0_TGRAN_SUPPORTED ID_AA64MMFR0_TGRAN16_SUPPORTED
#elif defined(IVY_CFG_ARM64_64K_PAGES)
#define ID_AA64MMFR0_TGRAN_SHIFT ID_AA64MMFR0_TGRAN64_SHIFT
#define ID_AA64MMFR0_TGRAN_SUPPORTED ID_AA64MMFR0_TGRAN64_SUPPORTED
#endif

#define ID_AA64PFR0_EL2_SHIFT 8

#define TCR_IPS_SHIFT 32
#define TCR_IPS_MASK (UL(7) << TCR_IPS_SHIFT)

// 支持的最大物理地址位置，不使用52位时，最大为48，目前只支持48
// #ifdef CONFIG_ARM64_PA_BITS_52
// #define ID_AA64MMFR0_PARANGE_MAX	ID_AA64MMFR0_PARANGE_52
// #else
#define ID_AA64MMFR0_PARANGE_MAX ID_AA64MMFR0_PARANGE_48
// #endif

/* Current Exception Level values, as contained in CurrentEL */
#define CurrentEL_EL1 (1 << 2)
#define CurrentEL_EL2 (2 << 2)
#define CurrentEL_EL3 (3 << 2)

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
