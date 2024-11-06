// Copyright 2024 zuoqian, zuoqian@qq.com

#include "dummy_uart.h"

void dummy_uart_putchar(unsigned long base, char c) {
  volatile unsigned long *pb = (unsigned long *)base;
  *pb = c;
}
