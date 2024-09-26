# author : zuoqian
# Copyright 2024. All rights reserved.

import logging
import argparse
import random
import math
from dataclasses import dataclass
from enum import Enum
from mint import moesi
from mint.moesi import Cacheline
import purslane
from purslane.dsl import Do, Action, Sequence, Parallel, Select, Run, TypeOverride
from purslane.dsl import RandU8, RandU16, RandU32, RandU64, RandUInt, RandS8, RandS16, RandS32, RandS64, RandInt
from purslane.addr_space import AddrSpace
from purslane.addr_space import SMWrite8, SMWrite16, SMWrite32, SMWrite64, SMWriteBytes
from purslane.addr_space import SMRead8, SMRead16, SMRead32, SMRead64, SMReadBytes

# 获取目标平台配置
# import ivy_app_cfg

logger = logging.getLogger('stressapp')


@dataclass
class AdlerChecksum:
    a1: int
    a2: int
    b1: int
    b2: int


@dataclass
class PatternData:
    name: str
    data: list[int]


WALKING_ONES_DATA = [
    0x00000001, 0x00000002, 0x00000004, 0x00000008,
    0x00000010, 0x00000020, 0x00000040, 0x00000080,
    0x00000100, 0x00000200, 0x00000400, 0x00000800,
    0x00001000, 0x00002000, 0x00004000, 0x00008000,
    0x00010000, 0x00020000, 0x00040000, 0x00080000,
    0x00100000, 0x00200000, 0x00400000, 0x00800000,
    0x01000000, 0x02000000, 0x04000000, 0x08000000,
    0x10000000, 0x20000000, 0x40000000, 0x80000000,
    0x40000000, 0x20000000, 0x10000000, 0x08000000,
    0x04000000, 0x02000000, 0x01000000, 0x00800000,
    0x00400000, 0x00200000, 0x00100000, 0x00080000,
    0x00040000, 0x00020000, 0x00010000, 0x00008000,
    0x00004000, 0x00002000, 0x00001000, 0x00000800,
    0x00000400, 0x00000200, 0x00000100, 0x00000080,
    0x00000040, 0x00000020, 0x00000010, 0x00000008,
    0x00000004, 0x00000002, 0x00000001, 0x00000000
]

WALKINGS_ONES = PatternData(name='walking_ones', data=WALKING_ONES_DATA)

WALKING_INV_ONES_DATA = [
    0x00000001, 0xfffffffe, 0x00000002, 0xfffffffd,
    0x00000004, 0xfffffffb, 0x00000008, 0xfffffff7,
    0x00000010, 0xffffffef, 0x00000020, 0xffffffdf,
    0x00000040, 0xffffffbf, 0x00000080, 0xffffff7f,
    0x00000100, 0xfffffeff, 0x00000200, 0xfffffdff,
    0x00000400, 0xfffffbff, 0x00000800, 0xfffff7ff,
    0x00001000, 0xffffefff, 0x00002000, 0xffffdfff,
    0x00004000, 0xffffbfff, 0x00008000, 0xffff7fff,
    0x00010000, 0xfffeffff, 0x00020000, 0xfffdffff,
    0x00040000, 0xfffbffff, 0x00080000, 0xfff7ffff,
    0x00100000, 0xffefffff, 0x00200000, 0xffdfffff,
    0x00400000, 0xffbfffff, 0x00800000, 0xff7fffff,
    0x01000000, 0xfeffffff, 0x02000000, 0xfdffffff,
    0x04000000, 0xfbffffff, 0x08000000, 0xf7ffffff,
    0x10000000, 0xefffffff, 0x20000000, 0xdfffffff,
    0x40000000, 0xbfffffff, 0x80000000, 0x7fffffff,
    0x40000000, 0xbfffffff, 0x20000000, 0xdfffffff,
    0x10000000, 0xefffffff, 0x08000000, 0xf7ffffff,
    0x04000000, 0xfbffffff, 0x02000000, 0xfdffffff,
    0x01000000, 0xfeffffff, 0x00800000, 0xff7fffff,
    0x00400000, 0xffbfffff, 0x00200000, 0xffdfffff,
    0x00100000, 0xffefffff, 0x00080000, 0xfff7ffff,
    0x00040000, 0xfffbffff, 0x00020000, 0xfffdffff,
    0x00010000, 0xfffeffff, 0x00008000, 0xffff7fff,
    0x00004000, 0xffffbfff, 0x00002000, 0xffffdfff,
    0x00001000, 0xffffefff, 0x00000800, 0xfffff7ff,
    0x00000400, 0xfffffbff, 0x00000200, 0xfffffdff,
    0x00000100, 0xfffffeff, 0x00000080, 0xffffff7f,
    0x00000040, 0xffffffbf, 0x00000020, 0xffffffdf,
    0x00000010, 0xffffffef, 0x00000008, 0xfffffff7,
    0x00000004, 0xfffffffb, 0x00000002, 0xfffffffd,
    0x00000001, 0xfffffffe, 0x00000000, 0xffffffff
]

WALKING_INV_ONES = PatternData(
    name='walking_inv_ones', data=WALKING_INV_ONES_DATA)

WALKING_ZEROS_DATA = [
    0xfffffffe, 0xfffffffd, 0xfffffffb, 0xfffffff7,
    0xffffffef, 0xffffffdf, 0xffffffbf, 0xffffff7f,
    0xfffffeff, 0xfffffdff, 0xfffffbff, 0xfffff7ff,
    0xffffefff, 0xffffdfff, 0xffffbfff, 0xffff7fff,
    0xfffeffff, 0xfffdffff, 0xfffbffff, 0xfff7ffff,
    0xffefffff, 0xffdfffff, 0xffbfffff, 0xff7fffff,
    0xfeffffff, 0xfdffffff, 0xfbffffff, 0xf7ffffff,
    0xefffffff, 0xdfffffff, 0xbfffffff, 0x7fffffff,
    0xbfffffff, 0xdfffffff, 0xefffffff, 0xf7ffffff,
    0xfbffffff, 0xfdffffff, 0xfeffffff, 0xff7fffff,
    0xffbfffff, 0xffdfffff, 0xffefffff, 0xfff7ffff,
    0xfffbffff, 0xfffdffff, 0xfffeffff, 0xffff7fff,
    0xffffbfff, 0xffffdfff, 0xffffefff, 0xfffff7ff,
    0xfffffbff, 0xfffffdff, 0xfffffeff, 0xffffff7f,
    0xffffffbf, 0xffffffdf, 0xffffffef, 0xfffffff7,
    0xfffffffb, 0xfffffffd, 0xfffffffe, 0xffffffff
]
WALKING_ZEROS = PatternData(name='walking_zeros', data=WALKING_ZEROS_DATA)

ONE_ZERO_DATA = [0x00000000, 0xffffffff]
ONE_ZERO = PatternData(name='one_zero', data=ONE_ZERO_DATA)

JUST_ZERO_DATA = [0x00000000, 0x00000000]
JUST_ZERO = PatternData(name="just_zero", data=JUST_ZERO_DATA)

JUST_ONE_DATA = [0xffffffff, 0xffffffff]
JUST_ONE = PatternData(name='just_one', data=JUST_ONE_DATA)

JUST_FIVE_DATA = [0x55555555, 0x55555555]
JUST_FIVE = PatternData(name='just_five', data=JUST_FIVE_DATA)

JUST_A_DATA = [0xaaaaaaaa, 0xaaaaaaaa]
JUST_A = PatternData(name='just_a', data=JUST_A_DATA)

FIVE_A_DATA = [0x55555555, 0xaaaaaaaa]
FIVE_A = PatternData(name='five_a', data=FIVE_A_DATA)

FIVE_A8_DATA = [0x5aa5a55a, 0xa55a5aa5, 0xa55a5aa5, 0x5aa5a55a]
FIVE_A8 = PatternData(name='five_a8', data=FIVE_A8_DATA)

LONG_8b10b_DATA = [0x16161616, 0x16161616]
LONG_8b10b = PatternData(name='long_8b10b', data=LONG_8b10b_DATA)

SHORT_8b10b_DATA = [0xb5b5b5b5, 0xb5b5b5b5]
SHORT_8b10b = PatternData(name='short_8b10b', data=SHORT_8b10b_DATA)

CHECKER_8b10b_DATA = [0xb5b5b5b5, 0x4a4a4a4a]
CHECKER_8b10b = PatternData(name='checker_8b10b', data=CHECKER_8b10b_DATA)

FIVE7_DATA = [0x55555557, 0x55575555]
FIVE7 = PatternData(name='five7', data=FIVE7_DATA)

ZERO2FD_DATA = [0x00020002, 0xfffdfffd]
ZERO2FD = PatternData(name='zero2fd', data=ZERO2FD_DATA)

PATTERN_ARRAY = [WALKINGS_ONES,
                 WALKING_INV_ONES,
                 WALKING_ZEROS,
                 ONE_ZERO,
                 JUST_ZERO,
                 JUST_ONE,
                 JUST_FIVE,
                 JUST_A,
                 FIVE_A,
                 FIVE_A8,
                 LONG_8b10b,
                 SHORT_8b10b,
                 CHECKER_8b10b,
                 FIVE7,
                 ZERO2FD]

class Pattern:
    def __init__(self, pd: PatternData, bus_width: int, inverse: bool, idx: int) -> None:
        self.pattern_data = pd
        self.bus_width = bus_width
        self.inverse = inverse
        self.idx = idx

        if self.inverse:
            inverse_str = '_ivt_'
        else:
            inverse_str = ''

        self.name = f'{self.pattern_data.name}{inverse_str}{self.bus_width}'

        match self.bus_width:
            case 32:
                self.bus_shift = 0
            case 64:
                self.bus_shift = 1
            case 128:
                self.bus_shift = 2
            case 256:
                self.bus_shift = 3
            case _:
                logger.fatal('illegal bus width')

        self.CacculateCrc()

    # self.bus_shift allows for repeating each pattern word 1, 2, 4, etc. times.
    # in order to create patterns of different width.
    def Data(self, offset: int) -> int:
        offset = (offset >> self.bus_shift) % len(self.pattern_data.data)
        ret = self.pattern_data.data[offset]
        if self.inverse:
            mask = (1<<32) - 1
            ret = (~ret)&mask
        return ret
    
    def Len(self) -> int:
        return len(self.pattern_data) << self.bus_shift

    def CacculateCrc(self) -> None:
        a1 = 1
        a2 = 1
        b1 = 0
        b2 = 0

        blocksize = 4096
        count = blocksize/4

        i = 0
        while i < count:
            a1 += self.Data(i)
            b1 += a1
            i += 1
            a1 += self.Data(i)
            b1 += a1
            i += 1

            a2 += self.Data(i)
            b2 += a2
            i += 1
            a2 += self.Data(i)
            b2 += a2
            i += 1

        self.crc = AdlerChecksum(a1=a1, a2=a2, b1=b1, b2=b2)


class PatternList:
    def __init__(self) -> None:
        self.patterns = []
        for idx, pd in enumerate(PATTERN_ARRAY):
            self.patterns.append(Pattern(pd, 32, False, idx))
            self.patterns.append(Pattern(pd, 64, False, idx))
            self.patterns.append(Pattern(pd, 128, False, idx))
            self.patterns.append(Pattern(pd, 256, False, idx))

            self.patterns.append(Pattern(pd, 32, True, idx))
            self.patterns.append(Pattern(pd, 64, True, idx))
            self.patterns.append(Pattern(pd, 128, True, idx))
            self.patterns.append(Pattern(pd, 256, True, idx))
    
    def GetRandomPattern(self) -> Pattern:
        return random.choice(self.patterns)

PATTERN_LIST = PatternList()

print(PATTERN_LIST.patterns[0].crc)

BUFFER_SIZE = 1024
PARALLEL_MIN = 12
PARALLEL_MAX = 24


class Buffer:
    def __init__(self, addr: int) -> None:
        self.addr = addr
        self.valid = False


class BufferPool:
    def __init__(self, addr_space: AddrSpace) -> None:
        self._bufs = []
        self._bufs_work = []
        for i in range(PARALLEL_MAX*4):
            self._bufs.append(addr_space.AllocRandom(BUFFER_SIZE, 64))

    def GetEmpty(self) -> Buffer:
        pass

    def GetValid(self) -> Buffer:
        pass

    def Restore(elf) -> None:
        pass

class Fill(Action):
    def __init__(self, name: str = None) -> None:
        super().__init__(name)

class Copy(Action):
    def __init__(self, bufs: list[Buffer], name: str = None) -> None:
        super().__init__(name)

        # self.src =
        # self.dst =
        self.dst.valid = True

    def Body(self):
        pass


class Invert(Action):
    def __init__(self, buf: Buffer, name: str = None) -> None:
        super().__init__(name)
        self.buf = buf

    def Body(self):
        pass

class Check(Action):
    def __init__(self, name: str = None) -> None:
        super().__init__(name)


class Model(Action):
    def __init__(self, addr_space: AddrSpace, name: str = None) -> None:
        super().__init__(name)
        self.addr_space = addr_space
        self.bufs = []
        for i in range(128):
            self.bufs.append(self.addr_space.AllocRandom(BUFFER_SIZE, 64))

    def Activity(self):
        for i in range(2):
            # restore
            bufs = self.bufs

            num_para = random.randrange(PARALLEL_MIN, PARALLEL_MAX+1)
            with Parallel():
                for j in range(num_para):
                    match(random.randrange(0, 2)):
                        case 0:
                            pass
                        case 1:
                            pass
