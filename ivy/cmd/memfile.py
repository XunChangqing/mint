#  Copyright 2024 zuoqian, zuoqian@qq.com
# 
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
# 
#  https://www.apache.org/licenses/LICENSE-2.0
# 
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

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
