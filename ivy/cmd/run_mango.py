# author: zuoqian
# Copyright 2024. All rights reserved.

# 创建操作系统可以引导的 uimage 时需要起始地址

import argparse
import subprocess
import ivy_app_cfg
from xpk import bcfg

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument("--seed", help="random seed", type=int, required=True)
  parser.add_argument("--root", help="root component", type=str, required=True)
  parser.add_argument("--entry", help="entry action", type=str, required=True)
  parser.add_argument("--builtin_executors", help="use builtin executors", action='store_true')
  parser.add_argument("--soc_output", help="soc output name", type=str, required=True)
  parser.add_argument("inputs", help="inputs", nargs='+')
  args = parser.parse_args()

  arg_num_executors = f' --num_executors {ivy_app_cfg.NR_CPUS} '
  if(args.builtin_executors):
    arg_num_executors = ''
  
  mango_cmd = f'mango --seed {args.seed} --root {args.root} --entry {args.entry} {arg_num_executors} --soc_output {args.soc_output} --soc_cooperative {" ".join(args.inputs)}'
  print(mango_cmd)
  subprocess.run(mango_cmd, shell=True)