# author : zuoqian
# Copyright 2024. All rights reserved.

# 生成存储延迟测试的随机数组

import argparse
import os
import io
import math
from datasize import DataSize

# ivy app 配置变量
import ivy_app_cfg
# 激励配置
import numpy as np

# 激励配置常量
# range of memory access
# LEN = 128*xcg.SIZE_MB
# LEN = 128*xcg.SIZE_KB
# LEN = 8*xcg.SIZE_MB
# size of cacheline, bytes
# LINE = 64
# assert (LEN % LINE == 0)

# @dataclass_json
# @dataclass
# class ScenCfg:
#     len: int = 8*xcg.SIZE_MB
#     line: int = 64

def words_init(num_word, scale):
  words = [0]*num_word
  nbits = num_word.bit_length()-1
  # print(nbits)
  for i in range(num_word):
    for j in range(nbits):
      if i & (1 << j):
        words[i] |= (1 << nbits-j-1)

  print(words)
  return [w*scale for w in words]

def create_circular_list(page_size: int, len: int, line: int):
  assert (len % line == 0)
  assert (page_size % line == 0)
  ptrs = [0]*int(len/8)
  head = None

  # words和pages都是字节数
  if len % page_size != 0:
    num_words = int(len/line)
    words = words_init(num_words, line)
    for i in range(num_words-1):
      # print(int(words[i]/8))
      ptrs[int(words[i]/8)] = words[i+1]
    ptrs[int(words[-1]/8)] = 0
    # 索引号
    head = 0
  else:
    num_words = int(page_size/line)
    num_page = int((len+page_size-1)/page_size)
    words = words_init(num_words, line)
    pages = np.random.permutation(num_page)
    pages = [p*page_size for p in pages]

    for i in range(num_page-1):
      cpage = pages[i]
      npage = pages[i+1]
      for j in range(num_words):
        cur = cpage + words[(i+j) % num_words]
        next = npage + words[(i+j+1) % num_words]
        ptrs[int(cur/8)] = next

    i = num_page - 1
    cpage = pages[-1]
    npage = pages[0]
    for j in range(num_words):
      cur = cpage + words[(i+j) % num_words]
      next = npage + words[(j+1) % num_words]
      ptrs[int(cur/8)] = next
    head = int(pages[0]/8)

  return head, ptrs

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument("--length", help="test length", type=str, required=True)
  parser.add_argument("--line", help="cache line size", type=str, required=True)
  args = parser.parse_args()

  length = DataSize(args.length)
  line = DataSize(args.line)
  print(f'memlat len {length:B} line {line:B}')

  if length % line != 0:
    raise Exception('len should be divisible by line')

  head, ptrs = create_circular_list(ivy_app_cfg.PAGE_SIZE, length, line)

  # 遍历一圈检查
  cnt = 0
  cur = head
  while True:
    print(f'cur {cur}')
    cur = ptrs[cur]
    cur = int(cur/8)
    cnt += 1
    if cur == head:
        break
  print("OK", cnt)

  times_per_iter = math.ceil((length/line)/100)
  print("times per iter: ", times_per_iter)
  print("test times: ", times_per_iter*100*8)

  # 数据写入内存文件, 注意只有索引,运行时需要加上基地址便宜
  with open('data.S', 'w') as f:
    f.write('\t.align 8\n')
    f.write('\t.section\t".data"\n')
    f.write('.global lat_data\n')
    f.write('lat_data:\n')
    for ptr in ptrs:
      # print(f'ptr {ptr:#x}')
      # f.write((int(ptr)).to_bytes(8, 'little', signed=False))
      f.write(f'\t.quad\tlat_data+{int(ptr)}\n')

  with open('memlat_cfg.h', 'w') as f:
    f.write('#pragma once\n')
    f.write("#define HEAD ({:#x})\n\n".format(head))
    f.write("#define WARMUP_TIMES ({})\n".format(times_per_iter))
    f.write("#define TEST_TIMES ({})\n\n".format(times_per_iter*8))
    f.write("#define NUM_PTR ({})\n\n".format(len(ptrs)))

