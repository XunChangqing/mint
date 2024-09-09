// author : zuoqian
// Copyright 2023. All rights reserved.

#include "dummy_uart.h"

void dummy_uart_putchar(uint64_t base, char c) {
  volatile uint64_t *pb = (uint64_t *)base;
  *pb = c;
}
