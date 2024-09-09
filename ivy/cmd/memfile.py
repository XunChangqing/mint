# author: zuoqian
# Copyright 2024. All rights reserved.

# 创建 ivy_mem_files.h ,用于 c 程序访问内存文件的起始位置和尺寸

import argparse
import re
from pathlib import Path

def make_c_id(s):
  return re.sub(r'\W+', '_', s)

def Main():
  parser = argparse.ArgumentParser()
  parser.add_argument("-F", help="file", type=str, dest='files', action='append')
  args = parser.parse_args()

  print('memory files: ', args.files)

  with open('ivy_mem_files.h', 'w') as f:
    f.write('#pragma once\n')
    f.write('extern int text_end;\n')
    pos = 0
    idx = 0
    if args.files:
      for fn in args.files:
        p = Path(fn)
        name = f'{make_c_id(p.name)}'.upper()
        
        size = p.stat().st_size
        f.write(f'#define IVY_MEM_FILE_{idx}_{name}_START ((char*)(&text_end)+{pos})\n')
        f.write(f'#define IVY_MEM_FILE_{idx}_{name}_SIZE ({size})\n')

        pos += size
        idx += 1
