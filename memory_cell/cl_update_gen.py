# author : zuoqian
# Copyright 2024. All rights reserved.

# 辅助生成一些代码

cl_sizes = [1,2,4,8,16,32,64]

with open('build/cl_update_gen.c', 'w')  as f:
  first = True
  for cs in cl_sizes:
    if first:
      f.write(f'if')
    else:
      f.write('else if')
    first = False
    f.write(f'(cl_access.size == {cs})\n')
    f.write('{\n')
    offset_first = True
    for offset in range(0, 64, cs):
      if offset_first:
        f.write('if')
      else:
        f.write('else if')
      offset_first = False
      f.write(f'(cl_access.offset == {offset})\n')
      f.write('{\n')
      f.write(f'comp.cl_val[{(offset+cs)*8-1}:{offset*8}] = val[{(offset+cs)*8-1}:{offset*8}];\n')
      f.write('}\n')
    f.write('}\n')

# for i in range(512, 0, -64):
#   print(i-1, i-64)

def gen_mem_func(f, func_name, mem_func_name):
  f.write(f'static void {func_name}(uintptr_t addr, uint32_t offset, uint32_t size, uint64_t v0, uint64_t v1, uint64_t v2, uint64_t v3, uint64_t v4, uint64_t v5, uint64_t v6, uint64_t v7){{\n')

  f.write('switch(size){\n')
  for cs in cl_sizes:
    f.write(f'case {cs}:\n')
    f.write('switch(offset){\n')
    for offset in range(0, 64, cs):
      f.write(f'case({offset}):\n')
      if cs < 8:
        f.write(f'{mem_func_name}{cs*8}(addr+offset, v{int(offset/8)}>>({(offset%8)*8}));\n')
      else:
        f.write(f'{mem_func_name}{cs*8}(addr+offset ')
        for csidx in range(0, int(cs/8)):
          f.write(f', v{csidx+int(offset/8)}')
        f.write(');\n')

      f.write('break;\n')

    f.write('default:\n')
    f.write('break;\n')
    f.write('}\n')

    f.write('break;\n')

  f.write('default:\n')
  f.write('break;\n')
  f.write('}\n')

  f.write('}\n')


with open('build/c_gen.c', 'w') as f:
  gen_mem_func(f, 'write_cl', 'mem_write')
  gen_mem_func(f, 'read_check_cl', 'mem_read_check')
