#pragma once

// 以下几个 bar[4] 基地址的寄存器可以任意读写，可以作为 ram 进行测试
// the registers below based on bar[4] can be read/write randomly

#define ZNI_REG_RM_VP_TYPE 0x840
#define ZNI_REG_RM_MPQ_TYPE 0x850
#define ZNI_REG_RM_EQ_TYPE 0x860
#define ZNI_REG_RM_ATT_BASE 0x870
