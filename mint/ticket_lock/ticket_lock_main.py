# author : zuoqian
# Copyright 2024. All rights reserved.

import ivy_app_cfg
import logging
import argparse
import random
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
# K11.2.1 Message passing
    # resolving weakly-ordered message passing by using Acquire and Release
# K11.6.1
    # Message passing
# P1
    # STR R5, [R1] R5-0x55555555555555
    # STL R0, [R2]
# P2
    # WAIT_ACQ([R2] == 1)
    # LDR R5, [R1]
    # R5 == 0x5555555555555555 must be guaranteed

# v1，定向激励
# v2，场景随机，可以测试到不同处理核
# v3，指令随机，可以测试到不同寄存器
# v4，指令噪音
# v5，场景噪音

addr_space = purslane.addr_space.AddrSpace()
for mr in ivy_app_cfg.free_mem_ranges:
    addr_space.AddNode(mr.base, mr.size, mr.numa_id)
nr_cpus = ivy_app_cfg.NR_CPUS

from mint.models import stressapp
from mint.c_stressapp import c_stressapp
import mint.ticket_lock.ticket_lock_v4 as tl

tl.addr_space = addr_space
tl.nr_cpus = nr_cpus

# 获取目标平台配置
# import ivy_app_cfg

logger = logging.getLogger('ticket_lock_main')

ITERS = 16

class Entry(Action):
    # combine swo with stressapp
    def __init__(self, name: str = None) -> None:
        super().__init__(name)

    def Activity(self):
        stressapp.BATCH_NUM = int(ITERS/8)
        stressapp.PAGE_SIZE = 4096
        stressapp.PAGE_NUM = nr_cpus*6
        pages = [stressapp.Page(addr_space.AllocRandom(stressapp.PAGE_SIZE, 64))
                 for i in range(stressapp.PAGE_NUM)]

        with Parallel():
            Do(c_stressapp.CStressApp(pages))
            Do(tl.Entry(ITERS))


def Main():
    logging.basicConfig(level=logging.INFO)

    print(random.getrandbits(31))

    parser = argparse.ArgumentParser()
    purslane.dsl.PrepareArgParser(parser)
    parser.add_argument('--stress', action='store_true')

    args = parser.parse_args()
    if args.seed is not None:
        rand_seed = args.seed
    else:
        rand_seed = random.getrandbits(31)
    random.seed(rand_seed)
    logger.info(f'random seed is {rand_seed}')

    args.num_executors = ivy_app_cfg.NR_CPUS

    if args.stress:
        logger.info('stress')
        Run(Entry(), args)
    else:
        Run(tl.Entry(ITERS), args)

if __name__ == '__main__':
    Main()
