# author : zuoqian
# Copyright 2024. All rights reserved.

import ivy_app_cfg
import logging
import argparse
import typing
import random
import math
import atexit
from dataclasses import dataclass
from enum import Enum
import purslane
from purslane.dsl import Do, Action, Sequence, Parallel, Schedule, Select, Run, TypeOverride
from purslane.dsl import RandU8, RandU16, RandU32, RandU64, RandUInt, RandS8, RandS16, RandS32, RandS64, RandInt
from purslane.addr_space import AddrSpace
from purslane.addr_space import SMWrite8, SMWrite16, SMWrite32, SMWrite64, SMWriteBytes
from purslane.addr_space import SMRead8, SMRead16, SMRead32, SMRead64, SMReadBytes
import purslane.dsl
from purslane.aarch64.instr_stream import PushStackStream, PopStackStream, RandLoadStoreStream, SubProc

# DDI0487Fc_armv8_arm.pdf
# K11.6.1 Simple ordering and barrier class
# P1
#     STR R5, [R1]
#     DMB
#     LDR R6, [R2]
#     check
# P2
#     STR R6, [R2]
#     DMB
#     LDR R5, [R1]
#     check

# v1，定向激励
# v2，场景随机，可以测试到不同处理核
# v3，指令随机，可以测试到不同寄存器
# v4，指令噪音
# v5，场景噪音

import mint.simple_weakly_ordering.swo_v4 as swo

# 获取目标平台配置
# import ivy_app_cfg

logger = logging.getLogger('swo_main')


def Main():
    logging.basicConfig(level=logging.INFO)

    print(random.getrandbits(31))

    parser = argparse.ArgumentParser()
    purslane.dsl.PrepareArgParser(parser)

    args = parser.parse_args()
    if args.seed is not None:
        rand_seed = args.seed
    else:
        rand_seed = random.getrandbits(31)
    random.seed(rand_seed)
    logger.info(f'random seed is {rand_seed}')

    args.num_executors = ivy_app_cfg.NR_CPUS

    Run(swo.Entry(), args)


if __name__ == '__main__':
    Main()
