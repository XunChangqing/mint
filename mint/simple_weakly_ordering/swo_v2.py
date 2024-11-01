# author : zuoqian
# Copyright 2024. All rights reserved.

import ivy_app_cfg
import logging
import random
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
from purslane.aarch64 import v8

# 获取目标平台配置
# import ivy_app_cfg

logger = logging.getLogger('swo_v2')

addr_space: AddrSpace = None
nr_cpus: int = None

rf = open('rand_proc.S', 'w')
atexit.register(rf.close)

rf.write('#include <linux/linkage.h>\n')

# class MessagePassingAR(Action):
#     # resolving weakly-ordered message passing by using Acquire and Release
#     def __init__(self, name: str = None) -> None:
#         super().__init__(name)

#     def Activity(self):
#         # init
#         # parallel sender observer
#         pass


class SimpleWeaklyOrderingInit(Action):
    def __init__(self, addr_a: int, addr_b: int, name: str = None) -> None:
        super().__init__(name)
        self.addr_a = addr_a
        self.addr_b = addr_b

    def Body(self):
        self.c_src = f'WRITE_ONCE(*(uint64_t*){self.addr_a}, 0);\n'
        self.c_src += f'WRITE_ONCE(*(uint64_t*){self.addr_b}, 0);\n'


class SimpleWeaklyOrderingP1(Action):
    def __init__(self, addr_a: int, addr_b: int, addr_c: int, name: str = None) -> None:
        super().__init__(name)
        self.addr_a = addr_a
        self.addr_b = addr_b
        self.addr_c = addr_c

    def Body(self):
        func_name = f'{self.name}_asm_func'
        with v8.proc(func_name, rf):
            v8.verbatim(f'ldr x1, ={self.addr_a:#x}')
            v8.verbatim(f'ldr x2, ={self.addr_b:#x}')
            v8.verbatim(f'ldr x5, ={0x5555555555555555:#x}')
            v8.verbatim(f'ldr x6, ={0x6666666666666666:#x}')
            # R1 <- addr_a
            # R2 <- addr_b

            # STR R5, [R1]
            v8.verbatim(f'str x5, [x1]')
            # LDR R6, [R2]
            v8.verbatim(f'ldr x6, [x2]')
            # noise
            # rf.write(f'')
            # R0 <- addr_c
            # STR R6, [R0] for checking
            v8.verbatim(f'ldr x0, ={self.addr_c:#x}')
            v8.verbatim(f'str x6, [x0]')

        self.c_src = f'{self.name}_asm_func();\n'


class SimpleWeaklyOrderingP2(Action):
    def __init__(self, addr_a: int, addr_b: int, addr_d: int, name: str = None) -> None:
        super().__init__(name)
        self.addr_a = addr_a
        self.addr_b = addr_b
        self.addr_d = addr_d

    def Body(self):
        func_name = f'{self.name}_asm_func'
        with v8.proc(func_name, rf):
            v8.verbatim(f'ldr x1, ={self.addr_a:#x}')
            v8.verbatim(f'ldr x2, ={self.addr_b:#x}')
            v8.verbatim(f'ldr x5, ={0x5555555555555555:#x}')
            v8.verbatim(f'ldr x6, ={0x6666666666666666:#x}')
            # R1 <- addr_a
            # R2 <- addr_b

            # STR R6, [R2]
            v8.verbatim(f'\tstr x6, [x2]\n')
            # LDR R5, [R1]
            v8.verbatim(f'\tldr x5, [x1]\n')
            # noise
            # rf.write(f'')
            # R0 <- addr_c
            # STR R6, [R0] for checking
            v8.verbatim(f'ldr x0, ={self.addr_d:#x}')
            v8.verbatim(f'str x5, [x0]')

        self.c_src = f'{self.name}_asm_func();\n'


class SimpleWeaklyOrderCheck(Action):
    def __init__(self, addr_c: int, addr_d: int, name: str = None) -> None:
        super().__init__(name)
        self.addr_c = addr_c
        self.addr_d = addr_d

    def Body(self):
        self.c_src = f'swo_check((uint64_t*){self.addr_c:#x}, (uint64_t*){self.addr_d:#x});\n'


class SimpleWeaklyOrdering(Action):
    def __init__(self, addr_a: int, addr_b: int, addr_c: int, addr_d: int, p1: int, p2: int, name: str = None) -> None:
        super().__init__(name)
        self.addr_a = addr_a
        self.addr_b = addr_b
        self.addr_c = addr_c
        self.addr_d = addr_d
        self.p1 = p1
        self.p2 = p2

    def Activity(self):
        # init
        Do(SimpleWeaklyOrderingInit(self.addr_a, self.addr_b))
        with Parallel():
            p1_act = SimpleWeaklyOrderingP1(
                self.addr_a, self.addr_b, self.addr_c)
            p2_act = SimpleWeaklyOrderingP2(
                self.addr_a, self.addr_b, self.addr_d)
            p1_act.executor_id = self.p1
            p2_act.executor_id = self.p2
            Do(p1_act)
            Do(p2_act)
        Do(SimpleWeaklyOrderCheck(self.addr_c, self.addr_d))


class Entry(Action):
    def __init__(self, iters:int = 2, name: str = None) -> None:
        super().__init__(name)
        self.iters = iters
        self.c_headers = ['#include <linux/compiler.h>', '#include "cfunc.h"']

    def Activity(self):
        for i in range(self.iters):
            cpus = [i for i in range(nr_cpus)]
            test_cpus = random.sample(cpus, 2)
            p1 = test_cpus[0]
            p2 = test_cpus[1]

            addr_a = addr_space.AllocRandom(8, 8)
            addr_b = addr_space.AllocRandom(8, 8)
            addr_c = addr_space.AllocRandom(8, 8)
            addr_d = addr_space.AllocRandom(8, 8)
            addr_space.Free(addr_a)
            addr_space.Free(addr_b)
            addr_space.Free(addr_c)
            addr_space.Free(addr_d)

            Do(SimpleWeaklyOrdering(addr_a, addr_b, addr_c, addr_d, p1, p2))
