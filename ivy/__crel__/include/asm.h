// author : zuoqian
// Copyright 2023. All rights reserved.

#pragma once

// #define __always_inline inline __attribute__((always_inline))

#define MRS_E(r, s) __asm__ volatile("mrs %0, " #s : "=r"(r))
#define MSR_E(s, r) __asm__ volatile("msr " #s ", %0" ::"r"(r))
#define MRS(r, s) MRS_E(r, s)
#define MSR(s, r) MSR_E(s, r)
#define MOV(r, s) __asm__ volatile("mov %0, " #s : "=r"(r))

#define ISB() __asm__ volatile("isb")
#define DSB() __asm__ volatile("dsb sy" ::: "memory")
#define WFI() __asm__ volatile("wfi" ::: "memory")
#define WFE() __asm__ volatile("wfe" ::: "memory")
#define SEV() __asm__ volatile("sev" ::: "memory")
#define NOP() __asm__ volatile("nop")

// #define sev()		asm volatile("sev" : : : "memory")
// #define wfe()		asm volatile("wfe" : : : "memory")
// #define wfi()		asm volatile("wfi" : : : "memory")

// #define isb()		asm volatile("isb" : : : "memory")
// #define dmb(opt)	asm volatile("dmb " #opt : : : "memory")
// #define dsb(opt)	asm volatile("dsb " #opt : : : "memory")

// #define mb()		dsb(sy)
// #define rmb()		dsb(ld)
// #define wmb()		dsb(st)

// #define dma_rmb()	dmb(oshld)
// #define dma_wmb()	dmb(oshst)

// #define __smp_mb()	dmb(ish)
// #define __smp_rmb()	dmb(ishld)
// #define __smp_wmb()	dmb(ishst)
