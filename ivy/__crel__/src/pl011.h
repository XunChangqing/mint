// author : zuoqian
// Copyright 2023. All rights reserved.

#pragma once

#include <linux/types.h>

/** @brief UART数据位的长度 */
// typedef enum {
//   kPl0115BitsPerchar = 0b00,
//   kPl0116BitsPerchar = 0b01,
//   kPl0117BitsPerchar = 0b10,
//   kPl0118BitsPerchar = 0b11,
// } pl011_datalen;

/**
 * @brief UART应用结构体，包含对UART的所有功能配置
 */
typedef struct {
  u32 baudrate;  ///<波特率
  u32 bitcount;  ///<数据位bit数 0b00, 0b01, 0b10, 0b11
  bool enablefifo;    ///<使能FIFO
  bool enableuart;    ///<使能UART
  bool enablerx;      ///<使能接收
  bool enabletx;      ///<使能发送
} pl011_cfg;

void pl011_init(unsigned long base, pl011_cfg *cfg);
void pl011_putchar(unsigned long base, char);
