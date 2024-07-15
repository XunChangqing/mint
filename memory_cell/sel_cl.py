# author : zuoqian
# Copyright 2024. All rights reserved.

import ivy_app_cfg

# 选取64个测试用的cacheline
NUM_CACHELINES = 64

STRIDE = 4*1024*1024

def pick_cl():
  fr_idx = 0
  offset = 0

  while True:
    cl_start = ivy_app_cfg.FREE_RANGES[fr_idx][0] + offset
    if(cl_start >= ivy_app_cfg.FREE_RANGES[fr_idx][1]):
      pass
    else:
      yield cl_start

    fr_idx += 1
    fr_idx = fr_idx % len(ivy_app_cfg.FREE_RANGES)
    if fr_idx == 0:
      offset += STRIDE

if __name__ == '__main__':
  with open('cl_def.h', 'w') as f:
    f.write('#pragma once\n')
    cl_gen = pick_cl()
    for i in range(0, NUM_CACHELINES):
      f.write(f'#define CL_{i} ({next(cl_gen):#x})\n')
