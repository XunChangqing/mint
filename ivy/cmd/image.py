# author: zuoqian
# Copyright 2024. All rights reserved.

# 创建操作系统可以引导的 uimage 时需要起始地址

import argparse
import subprocess
from pathlib import Path
import shutil
import ivy_app_cfg

def concatenate_files(file_list, output_file):
  with open(output_file, "wb") as outfile:
    for file in file_list:
      with open(file, "rb") as infile:
        shutil.copyfileobj(infile, outfile)

def Main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--name", help="name", type=str, required=True)
  parser.add_argument("--objcopy", help="objcopy cmd", type=str, required=True)
  parser.add_argument("--mem_files", "-F", help="mem files", type=str, action='append')
  args = parser.parse_args()

  image_file = f'{args.name}.image'
  objcopy_cmd = f'{args.objcopy} -O binary -S {args.name} {args.name}.image'
  mkimage_cmd = f'mkimage -A arm64 -O linux -T kernel -C none -a {ivy_app_cfg.TEXT_BASE:x} -e {ivy_app_cfg.TEXT_BASE:x} -n {args.name} -d {args.name}.image {args.name}.uimage'
  # 转换为 image 文件
  subprocess.run(objcopy_cmd, shell=True)

  if args.mem_files and len(args.mem_files) > 0:
    # 附加内存文件
    mem_files = args.mem_files
    cat_file = image_file+'.cat'
    print(f'mem files: {mem_files}')
    concatenate_files([image_file]+mem_files, cat_file)
    # 检查文件尺寸,不能超过 MAX_TEXT_SIZE
    cat_file_p = Path(cat_file)
    cat_file_p.rename(image_file)

  assert(Path(image_file).stat().st_size < ivy_app_cfg.MAX_TEXT_SIZE)
  # 转换为 uboot 引导文件
  subprocess.run(mkimage_cmd, shell=True)
