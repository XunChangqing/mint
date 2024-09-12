# author : zuoqian
# Copyright 2024. All rights reserved.

# 生成存储延迟测试的随机数组

import argparse
import os
import io
import math
import random

STRIDE = 4*1024*1024

# ivy app 配置变量
import ivy_app_cfg

# FREE_RANGES = [(0x40000000, 0x40080000, 0x0),(0x44080000, 0xc0000000, 0x0),]

if __name__ == '__main__':

  # 数据写入内存文件, 注意只有索引,运行时需要加上基地址
  with open('pattern.h', 'w') as f:
    f.write('uint64_t pattern_arr[] = {\n')
    for fr in ivy_app_cfg.FREE_RANGES:
      print(f'free range {fr[0]:#x} {fr[1]:#x}')
      for i in range(fr[0], fr[1], STRIDE):
        print(f'write pattern {i:#x}')
        f.write(f'0x{random.randbytes(8).hex()}, // addr {i:#x}\n')
    f.write('};\n')
