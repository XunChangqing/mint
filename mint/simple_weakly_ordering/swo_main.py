# author : zuoqian
# Copyright 2024. All rights reserved.

import ivy_app_cfg
import logging
import argparse
import random
import purslane
from purslane.dsl import Do, Action, Sequence, Parallel, Schedule, Select, Run, TypeOverride
from purslane.addr_space import AddrSpace
import purslane.dsl

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

from mint.models import stressapp
from mint.c_stressapp import c_stressapp
import mint.simple_weakly_ordering.swo_v4 as swo

addr_space = AddrSpace()
for mr in ivy_app_cfg.free_mem_ranges:
    addr_space.AddNode(mr.base, mr.size, mr.numa_id)
nr_cpus = ivy_app_cfg.NR_CPUS

swo.addr_space = addr_space
swo.nr_cpus = nr_cpus

logger = logging.getLogger('swo_main')

ITERS = 128

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
            Do(swo.Entry(ITERS))


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
        Run(swo.Entry(ITERS), args)


if __name__ == '__main__':
    Main()
