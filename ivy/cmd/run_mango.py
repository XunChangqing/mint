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