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

addr_space = AddrSpace()
for mr in ivy_app_cfg.free_mem_ranges:
    addr_space.AddNode(mr.base, mr.size, mr.numa_id)
nr_cpus = ivy_app_cfg.NR_CPUS

from mint.models import stressapp
from mint.c_stressapp import c_stressapp
import mint.lock_counter.lock_counter_v4 as lock_counter

lock_counter.addr_space = addr_space
lock_counter.nr_cpus = nr_cpus

# 获取目标平台配置
# import ivy_app_cfg

logger = logging.getLogger('ldst_excl_main')

ITERS = 32

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
            Do(lock_counter.Entry(ITERS))


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

    if args.stress:
        logger.info('stress')
        Run(Entry(), args)
    else:
        Run(lock_counter.Entry(ITERS), args)

if __name__ == '__main__':
    Main()
