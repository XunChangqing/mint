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

import ivy_app_cfg

logger = logging.getLogger('c_stressapp')


class DoFill(Action):
    def __init__(self, page: stressapp.Page, name: str = None) -> None:
        super().__init__(name)
        self.page = page

    def Body(self):
        pat = self.page.pattern
        pidx = pat.idx
        bus_shift = pat.bus_shift
        inverse = 1 if pat.inverse else 0
        self.c_src = f'fill((void*){self.page.addr:#x}, {stressapp.PAGE_SIZE}, {pidx}, {bus_shift}, {inverse});'


class DoCopy(Action):
    def __init__(self, src: stressapp.Page, dst: stressapp.Page, name: str = None) -> None:
        super().__init__(name)
        self.src = src
        self.dst = dst

    def Body(self):
        self.c_src = f'copy((void*){self.src.addr:#x}, (void*){self.dst.addr:#x}, {stressapp.PAGE_SIZE});'


class InvertUp(Action):
    def __init__(self, page: stressapp.Page, name: str = None) -> None:
        super().__init__(name)
        self.page = page

    def Body(self):
        self.c_src = f'invert_up((void*){self.page.addr:#x}, {stressapp.PAGE_SIZE});'


class InvertDown(Action):
    def __init__(self, page: stressapp.Page, name: str = None) -> None:
        super().__init__(name)
        self.page = page

    def Body(self):
        self.c_src = f'invert_down((void*){self.page.addr:#x}, {stressapp.PAGE_SIZE});'


class DoInvert(Action):
    def __init__(self, page: stressapp.Page, name: str = None) -> None:
        super().__init__(name)
        self.page = page

    def Activity(self):
        Do(InvertUp(self.page))
        Do(InvertDown(self.page))
        Do(InvertUp(self.page))
        Do(InvertDown(self.page))


class DoCheck(Action):
    def __init__(self, page: stressapp.Page, name: str = None) -> None:
        super().__init__(name)
        self.page = page

    def Body(self):
        assert (self.page.pattern)
        crc = self.page.pattern.crc
        self.c_src = f'check((void*){self.page.addr:#x}, {stressapp.PAGE_SIZE}, (struct adler_checksum){{.a1={crc.a1:#x}, .a2 = {crc.a2:#x}, .b1 = {crc.b1:#x}, .b2 = {crc.b2:#x} }});'


class CStressApp(Action):
    def __init__(self, pages: typing.List[stressapp.Page], name: str = None) -> None:
        super().__init__(name)
        self.pages = pages
        self.c_headers = ['#include <ivy/print.h>',
                          '#include <ivy/xrt.h>', '#include "worker.h"']

    def Activity(self):
        Do(stressapp.StressApp(self.pages))


def Main():
    logging.basicConfig(level=logging.INFO)

    addr_space = AddrSpace()

    for fr in ivy_app_cfg.FREE_RANGES:
        logger.info(f'addr space region: {fr[0]:#x}, {fr[1]:#x}')
        addr_space.AddNode(fr[0], fr[1]-fr[0]+1, fr[2])

    parser = argparse.ArgumentParser()
    purslane.dsl.PrepareArgParser(parser)

    parser.add_argument('--pclass', help='problem class of size')

    args = parser.parse_args()
    args.num_executors = ivy_app_cfg.NR_CPUS

    logger.info(f'problem class {args.pclass}')
    pclass = args.pclass
    match(pclass[0]):
        case 's' | 'S':
            stressapp.PAGE_SIZE = 4*1024
        case 'w' | 'W':
            stressapp.PAGE_SIZE = 1024*1024
        case 'a' | 'A':
            stressapp.PAGE_SIZE = 4*1024*1024
        case _:
            logger.critical(f'invalid problem class {pclass}')
            raise f'invalid problem class'
        
    stressapp.PAGE_NUM = args.num_executors * 6

    pages = [stressapp.Page(addr_space.AllocRandom(stressapp.PAGE_SIZE, 64))
             for i in range(stressapp.PAGE_NUM)]

    with (TypeOverride(stressapp.DoFill, DoFill),
          TypeOverride(stressapp.DoCheck, DoCheck),
          TypeOverride(stressapp.DoCopy, DoCopy),
          TypeOverride(stressapp.DoInvert, DoInvert)):
        Run(CStressApp(pages), args)


if __name__ == '__main__':
    Main()
