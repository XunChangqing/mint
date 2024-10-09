// author : zuoqian
// Copyright 2023. All rights reserved.

#pragma once

#include <linux/types.h>

void dw16550_init(unsigned long base_addr, unsigned int);
void dw16550_putchar(unsigned long base_addr, char c);
