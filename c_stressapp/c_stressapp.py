# author : zuoqian
# Copyright 2024. All rights reserved.

import logging
import argparse
import random
import math
from enum import Enum
import purslane
from purslane.dsl import Do, Action, Sequence, Parallel, Select, Run, TypeOverride
from purslane.dsl import RandU8, RandU16, RandU32, RandU64, RandUInt, RandS8, RandS16, RandS32, RandS64, RandInt
from purslane.addr_space import AddrSpace
from purslane.addr_space import SMWrite8, SMWrite16, SMWrite32, SMWrite64, SMWriteBytes
from purslane.addr_space import SMRead8, SMRead16, SMRead32, SMRead64, SMReadBytes

from mint import stressapp

import ivy_app_cfg

logger = logging.getLogger('c_stressapp')

PAGE_SIZE = 4096*2

class Page:
    def __init__(self, addr: int, pattern: stressapp.Pattern = None) -> None:
        self.addr = addr
        self.pattern = pattern


class Fill(Action):
    def __init__(self, page: Page, name: str = None) -> None:
        super().__init__(name)
        self.page = page
        self.page.pattern = stressapp.PATTERN_LIST.GetRandomPattern()

    def Body(self):
        pat = self.page.pattern
        pidx = pat.idx
        bus_shift = pat.bus_shift
        inverse = 1 if pat.inverse else 0
        self.c_src = f'fill((void*){self.page.addr:#x}, {PAGE_SIZE}, {pidx}, {bus_shift}, {inverse});'


class Check(Action):
    def __init__(self, page: Page, name: str = None) -> None:
        super().__init__(name)
        self.page = page

    def Body(self):
        crc = self.page.pattern.crc
        print(crc)
        self.c_src = f'check((void*){self.page.addr:#x}, {PAGE_SIZE}, (struct adler_checksum){{.a1={crc.a1:#x}, .a2 = {crc.a2:#x}, .b1 = {crc.b1:#x}, .b2 = {crc.b2:#x} }});'


class Model(Action):
    def __init__(self, page: Page, name: str = None) -> None:
        super().__init__(name)
        self.page = page
        self.c_headers = ['#include "print.h"', '#include "xrt.h"', '#include "worker.h"']

    def Activity(self):
        for i in range(4):
            Do(Fill(self.page))
            Do(Check(self.page))


def Main():
    logging.basicConfig(level=logging.INFO)

    addr_space = AddrSpace()

    for fr in ivy_app_cfg.FREE_RANGES:
        logger.info(f'addr space region: {fr[0]:#x}, {fr[1]:#x}')
        addr_space.AddNode(fr[0], fr[1]-fr[0]+1, fr[2])

    parser = argparse.ArgumentParser()
    purslane.dsl.PrepareArgParser(parser)

    args = parser.parse_args()
    args.num_executors = ivy_app_cfg.NR_CPUS

    if args.num_executors < 2:
        raise ('need more than one executor')
    
    page = Page(addr_space.AllocRandom(PAGE_SIZE, 64))

    Run(Model(page), args)

    # num_repeat_times = args.num_repeat_times
    # num_repeat_times = 64
    
    # moesi.NUM_EXECUTORS = args.num_executors
    # moesi.MAX_NUM_PARALLEL = 1
    # # moesi.NUM_EXECUTORS * 4
    # moesi.MIN_NUM_PARALLEL = 1
    # # moesi.NUM_EXECUTORS * 1

    # with (TypeOverride(moesi.Init, Init),
    #       TypeOverride(moesi.Read, Read),
    #       TypeOverride(moesi.Write, Write),
    #       TypeOverride(moesi.WriteNoAlloc, WriteNoAlloc),
    #       TypeOverride(moesi.Clean, Clean),
    #       TypeOverride(moesi.CleanInvalidate, CleanInvalidate),
    #       TypeOverride(moesi.CleanDomain, CleanDomain),
    #       TypeOverride(moesi.CleanInvalidateDomain, CleanInvalidateDomain)):
    #     Run(AArch64Moesi(num_repeat_times), args)


if __name__ == '__main__':
    Main()
