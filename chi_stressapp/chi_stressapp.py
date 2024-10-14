# author : zuoqian
# Copyright 2024. All rights reserved.

import logging
import argparse
import typing
import random
import math
from enum import Enum
import purslane
from purslane.dsl import Do, Action, Sequence, Parallel, Schedule, Select, Run, TypeOverride
from purslane.dsl import RandU8, RandU16, RandU32, RandU64, RandUInt, RandS8, RandS16, RandS32, RandS64, RandInt
from purslane.addr_space import AddrSpace
from purslane.addr_space import SMWrite8, SMWrite16, SMWrite32, SMWrite64, SMWriteBytes
from purslane.addr_space import SMRead8, SMRead16, SMRead32, SMRead64, SMReadBytes

from mint import stressapp

logger = logging.getLogger('chi_stressapp')


class DoFill(Action):
    def __init__(self, page: stressapp.Page, name: str = None) -> None:
        super().__init__(name)
        self.page = page

    def Body(self):
        pat = self.page.pattern
        pidx = pat.idx
        bus_shift = pat.bus_shift
        inverse = 1 if pat.inverse else 0
        # TODO
        self.sv_src = ''
        # self.c_src = f'fill((void*){self.page.addr:#x}, {stressapp.PAGE_SIZE}, {pidx}, {bus_shift}, {inverse});'


class DoCopy(Action):
    def __init__(self, src: stressapp.Page, dst: stressapp.Page, name: str = None) -> None:
        super().__init__(name)
        self.src = src
        self.dst = dst

    def Body(self):
        self.sv_src = ''
        # self.c_src = f'copy((void*){self.src.addr:#x}, (void*){self.dst.addr:#x}, {stressapp.PAGE_SIZE});'


class DoInvert(Action):
    def __init__(self, page: stressapp.Page, name: str = None) -> None:
        super().__init__(name)
        self.page = page

    def Body(self):
        self.sv_src = ''
        # self.c_src = f'invert((void*){self.page.addr:#x}, {stressapp.PAGE_SIZE});'


class DoCheck(Action):
    def __init__(self, page: stressapp.Page, name: str = None) -> None:
        super().__init__(name)
        self.page = page

    def Body(self):
        assert (self.page.pattern)
        crc = self.page.pattern.crc
        self.sv_src = ''
        # self.c_src = f'check((void*){self.page.addr:#x}, {stressapp.PAGE_SIZE}, (struct adler_checksum){{.a1={crc.a1:#x}, .a2 = {crc.a2:#x}, .b1 = {crc.b1:#x}, .b2 = {crc.b2:#x} }});'


def Main():
    logging.basicConfig(level=logging.INFO)

    addr_space = AddrSpace()

    # TODO
    # addr_space.AddNode()

    parser = argparse.ArgumentParser()
    purslane.dsl.PrepareArgParser(parser)

    args = parser.parse_args()

    if args.seed is not None:
        rand_seed = args.seed
    else:
        rand_seed = random.getrandbits(31)
    random.seed(rand_seed)
    logger.info(f'random seed is {rand_seed}')

    # args.num_executors = 2

    pages = [stressapp.Page(addr_space.AllocRandom(stressapp.PAGE_SIZE, 64))
             for i in range(stressapp.PAGE_NUM)]

    # num_repeat_times = args.num_repeat_times
    # num_repeat_times = 64

    # moesi.NUM_EXECUTORS = args.num_executors
    # moesi.MAX_NUM_PARALLEL = 1
    # # moesi.NUM_EXECUTORS * 4
    # moesi.MIN_NUM_PARALLEL = 1
    # # moesi.NUM_EXECUTORS * 1

    with (TypeOverride(stressapp.DoFill, DoFill),
          TypeOverride(stressapp.DoCheck, DoCheck),
          TypeOverride(stressapp.DoCopy, DoCopy),
          TypeOverride(stressapp.DoInvert, DoInvert)):
        Run(stressapp.StressApp(pages), args)

if __name__ == '__main__':
    Main()
