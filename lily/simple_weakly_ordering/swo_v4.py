# author : zuoqian
# Copyright 2024. All rights reserved.

import logging
import argparse
import typing
import random
import math
import atexit
from enum import Enum
from purslane.dsl import Do, Action, Sequence, Parallel, Schedule, Select, Run, TypeOverride
from purslane.dsl import RandU8, RandU16, RandU32, RandU64, RandUInt, RandS8, RandS16, RandS32, RandS64, RandInt
from purslane.addr_space import AddrSpace
from purslane.addr_space import SMWrite8, SMWrite16, SMWrite32, SMWrite64, SMWriteBytes
from purslane.addr_space import SMRead8, SMRead16, SMRead32, SMRead64, SMReadBytes
import purslane.dsl
from purslane.aarch64 import v8

# 获取目标平台配置
# import ivy_app_cfg

logger = logging.getLogger('swo_v4')

addr_space: AddrSpace = None
nr_cpus: int = None

rf = open('rand_proc.S', 'w')
atexit.register(rf.close)

rf.write('#include <linux/linkage.h>\n')

# ARM DDI 0487F.c (ID072120)
# K11. Barrier Litmus Tests

class SwoRsc:
    def __init__(self) -> None:
        self.addr_a: int = None
        self.addr_b: int = None
        self.addr_c: int = None
        self.addr_d: int = None
        self.p1: int = None
        self.p2: int = None
        self.p1_scratch_base: int = None
        self.p1_scratch_size: int = None
        self.p2_scratch_base: int = None
        self.p2_scratch_size: int = None

    def alloc(self, cpus_avail: typing.List):
        self.addr_a = addr_space.AllocRandom(8, 8)
        self.addr_b = addr_space.AllocRandom(8, 8)
        self.addr_c = addr_space.AllocRandom(8, 8)
        self.addr_d = addr_space.AllocRandom(8, 8)
        p1p2 = random.sample(cpus_avail, 2)
        self.p1 = p1p2[0]
        self.p2 = p1p2[1]
        cpus_avail.remove(self.p1)
        cpus_avail.remove(self.p2)
        self.p1_scratch_size = 4096
        self.p1_scratch_base = addr_space.AllocRandom(4096, 64)
        self.p2_scratch_size = 4096
        self.p2_scratch_base = addr_space.AllocRandom(4096, 64)

    def free(self):
        addr_space.Free(self.addr_a)
        addr_space.Free(self.addr_b)
        addr_space.Free(self.addr_c)
        addr_space.Free(self.addr_d)
        addr_space.Free(self.p1_scratch_base)
        addr_space.Free(self.p2_scratch_base)


class SimpleWeaklyOrderingInit(Action):
    def __init__(self, swo_rsc: SwoRsc, name: str = None) -> None:
        super().__init__(name)
        self.swo_rsc = swo_rsc

    def Body(self):
        addr_a = self.swo_rsc.addr_a
        addr_b = self.swo_rsc.addr_b
        self.c_src = f'WRITE_ONCE(*(uint64_t*){addr_a}, 0);\n'
        self.c_src += f'WRITE_ONCE(*(uint64_t*){addr_b}, 0);\n'

class SimpleWeaklyOrderingP1(Action):
    def __init__(self, swo_rsc: SwoRsc, name: str = None) -> None:
        super().__init__(name)
        self.swo_rsc = swo_rsc
        self.executor_id = swo_rsc.p1

    def Body(self):
        func_name = f'{self.name}_asm_func'
        r1_r, r2_r, r5_r, r6_r, r7_r = random.sample(v8.GPRS, 5)
        r1 = v8.reg_name(r1_r, True)
        r2 = v8.reg_name(r2_r, True)
        r5 = v8.reg_name(r5_r, True)
        r6 = v8.reg_name(r6_r, True)
        r7 = v8.reg_name(r7_r, True)

        addr_a = self.swo_rsc.addr_a
        addr_b = self.swo_rsc.addr_b
        addr_c = self.swo_rsc.addr_c

        # logger.info(f'p1 {r1} {r2} {r5} {r6} {r7}')

        with v8.proc(func_name, rf):
            v8.verbatim(f'ldr {r1}, ={addr_a:#x}')
            v8.verbatim(f'ldr {r2}, ={addr_b:#x}')
            v8.verbatim(f'ldr {r5}, ={0x5555555555555555:#x}')
            v8.verbatim(f'ldr {r6}, ={0x6666666666666666:#x}')
            # R1 <- addr_a
            # R2 <- addr_b

            # noise, reserve r1, r2, r5, r6
            v8.verbatim(f'// noise0')
            with v8.reserve([r1_r, r2_r, r5_r, r6_r, r7_r]):
                for i in range(random.randrange(4, 20)):
                    v8.arithm_imm()
            v8.verbatim('// noise end')

            # STR R5, [R1]
            v8.verbatim(f'str {r5}, [{r1}]')

            # noise
            v8.verbatim(f'// noise1')
            with v8.reserve([r1_r, r2_r, r5_r, r6_r, r7_r]):
                for i in range(random.randrange(0, 8)):
                    v8.arithm_imm()
            v8.verbatim('// noise end')

            # LDR R6, [R2]
            v8.verbatim(f'ldr {r6}, [{r2}]')

            # noise
            v8.verbatim(f'// noise2')
            with v8.reserve([r1_r, r2_r, r5_r, r6_r, r7_r]):
                for i in range(random.randrange(4, 20)):
                    v8.arithm_imm()
            v8.verbatim('// noise end')

            # R0 <- addr_c
            # STR R6, [R0] for checking
            v8.verbatim(f'ldr {r7}, ={addr_c:#x}')
            v8.verbatim(f'str {r6}, [{r7}]')

        self.c_src = f'{self.name}_asm_func();\n'


class SimpleWeaklyOrderingP2(Action):
    def __init__(self, swo_rsc: SwoRsc, name: str = None) -> None:
        super().__init__(name)
        self.swo_rsc = swo_rsc
        self.executor_id = swo_rsc.p2
    
    def Body(self):
        func_name = f'{self.name}_asm_func'

        r1_r, r2_r, r5_r, r6_r, r7_r = random.sample(v8.GPRS, 5)
        r1 = v8.reg_name(r1_r, True)
        r2 = v8.reg_name(r2_r, True)
        r5 = v8.reg_name(r5_r, True)
        r6 = v8.reg_name(r6_r, True)
        r7 = v8.reg_name(r7_r, True)

        addr_a = self.swo_rsc.addr_a
        addr_b = self.swo_rsc.addr_b
        addr_d = self.swo_rsc.addr_d

        with v8.proc(func_name, rf):
            v8.verbatim(f'ldr {r1}, ={addr_a:#x}')
            v8.verbatim(f'ldr {r2}, ={addr_b:#x}')
            v8.verbatim(f'ldr {r5}, ={0x5555555555555555:#x}')
            v8.verbatim(f'ldr {r6}, ={0x6666666666666666:#x}')
            # R1 <- addr_a
            # R2 <- addr_b

            # noise, reserve r1, r2, r5, r6
            v8.verbatim(f'// noise0')
            with v8.reserve([r1_r, r2_r, r5_r, r6_r, r7_r]):
                for i in range(random.randrange(4, 20)):
                    v8.arithm_imm()
            
            v8.verbatim('// noise end')

            # STR R6, [R2]
            v8.verbatim(f'str {r6}, [{r2}]')

            # noise
            v8.verbatim(f'// noise1')
            with v8.reserve([r1_r, r2_r, r5_r, r6_r, r7_r]):
                for i in range(random.randrange(0, 8)):
                    v8.arithm_imm()
            v8.verbatim('// noise end')

            # LDR R5, [R1]
            v8.verbatim(f'ldr {r5}, [{r1}]')

            # noise
            v8.verbatim(f'// noise2')
            with v8.reserve([r1_r, r2_r, r5_r, r6_r, r7_r]):
                for i in range(random.randrange(4, 20)):
                    v8.arithm_imm()
            v8.verbatim('// noise end')

            # R0 <- addr_c
            # STR R6, [R0] for checking
            v8.verbatim(f'ldr {r7}, ={addr_d:#x}')
            v8.verbatim(f'str {r5}, [{r7}]')

        self.c_src = f'{self.name}_asm_func();\n'


class SimpleWeaklyOrderCheck(Action):
    def __init__(self, swo_rsc: SwoRsc, name: str = None) -> None:
        super().__init__(name)
        self.swo_rsc = swo_rsc

    def Body(self):
        addr_c = self.swo_rsc.addr_c
        addr_d = self.swo_rsc.addr_d
        self.c_src = f'swo_check((uint64_t*){addr_c:#x}, (uint64_t*){addr_d:#x});\n'


class SimpleWeaklyOrdering(Action):
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
    def __init__(self, swo_rsc: SwoRsc, name: str = None) -> None:
        super().__init__(name)
        self.swo_rsc = swo_rsc

    def Activity(self):
        # init
        Do(SimpleWeaklyOrderingInit(self.swo_rsc))
        with Parallel():
            Do(SimpleWeaklyOrderingP1(self.swo_rsc))
            Do(SimpleWeaklyOrderingP2(self.swo_rsc))
        Do(SimpleWeaklyOrderCheck(self.swo_rsc))


class Entry(Action):
    def __init__(self, iters:int = 2, name: str = None) -> None:
        super().__init__(name)
        self.c_headers = ['#include <linux/compiler.h>', '#include "cfunc.h"']
        self.iters = iters

    def Activity(self):
        for i in range(self.iters):
            cpus = [i for i in range(nr_cpus)]
            swo_rsc = SwoRsc()
            swo_rsc.alloc(cpus)
            Do(SimpleWeaklyOrdering(swo_rsc))
            swo_rsc.free()
