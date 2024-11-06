# author : zuoqian
# Copyright 2024. All rights reserved.

import ivy_app_cfg
import logging
import argparse
import random
# from purslane.addr_space import Add
from purslane.addr_space import AddrSpace
from purslane.dsl import Do, Action, Sequence, Parallel, Schedule, Select, Run, TypeOverride
import purslane

# DDI0487Fc_armv8_arm.pdf
# K11.2.2 Address dependency with object construction
# when accessing an object-oriented data structure, the address dependency rule means that barriers are not required.
# even when initializing the object. A Store-Release can be used to ensure the order of the update of the base address.

# P1
    # STR W5, [X1, #offset] ; sets new data in a field
    # STLR X1, [X2]         ; updates base address
# P2
    # LDR X1, [X2]          ; reads base address
    # CMP X1, #0            ; check if it is valid
    # BEQ null_trap
    # LDR W5, [X1, #offset] ; uses base address to read field

    # it is required that P2:R5==0x55

# v1，定向激励
# v2，场景随机，可以测试到不同处理核
# v3，指令随机，可以测试到不同寄存器
# v4，指令噪音
# v5，场景噪音

addr_space = AddrSpace()
for mr in ivy_app_cfg.free_mem_ranges:
    addr_space.AddNode(mr.base, mr.size, mr.numa_id)
nr_cpus = ivy_app_cfg.NR_CPUS

from lily.models import stressapp
from lily.c_stressapp import c_stressapp
import lily.addr_dep_object_construction.adoc_v4 as adoc

adoc.addr_space = addr_space
adoc.nr_cpus = nr_cpus

# 获取目标平台配置
# import ivy_app_cfg

logger = logging.getLogger('adoc_main')

ITERS = 16

class Entry(Action):
    # combine adoc with stressapp
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
            Do(adoc.Entry(ITERS))


def Main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    purslane.dsl.PrepareArgParser(parser)
    parser.add_argument('--stress', action='store_true')
    parser.add_argument('--armv7', action='store_true')

    args = parser.parse_args()
    if args.seed is not None:
        rand_seed = args.seed
    else:
        rand_seed = random.getrandbits(31)
    random.seed(rand_seed)
    logger.info(f'random seed is {rand_seed}')

    args.num_executors = ivy_app_cfg.NR_CPUS

    if args.armv7:
        logger.info('armv7')
        adoc.armv7 = True
    else:
        logger.info('armv8')

    if args.stress:
        logger.info('stress')
        Run(Entry(), args)
    else:
        Run(adoc.Entry(ITERS), args)

if __name__ == '__main__':
    Main()
