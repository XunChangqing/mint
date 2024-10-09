// author : zuoqian
// Copyright 2023. All rights reserved.

#include "dummy_uart.h"

void dummy_uart_putchar(unsigned long base, char c) {
  volatile unsigned long *pb = (unsigned long *)base;
  *pb = c;
}
