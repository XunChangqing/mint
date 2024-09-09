// author : zuoqian
// Copyright 2023. All rights reserved.

#pragma once

#include <stdbool.h>
#include <stdint.h>

void dw16550_init(uint64_t, unsigned int);
void dw16550_putchar(uint64_t, char);
