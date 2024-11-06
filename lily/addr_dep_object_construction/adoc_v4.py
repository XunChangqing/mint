# author : zuoqian
# Copyright 2024. All rights reserved.

import logging
import typing
import random
import atexit
from enum import Enum
from purslane.dsl import Do, Action, Sequence, Parallel, Schedule, Select, Run, TypeOverride
from purslane.addr_space import AddrSpace
from purslane.aarch64 import v8

logger = logging.getLogger('adoc_v4')

addr_space: AddrSpace = None
nr_cpus: int = None
armv7: bool = False

rf = open('rand_proc.S', 'w')
atexit.register(rf.close)

rf.write('#include <linux/linkage.h>\n')

OBJECT_SIZE = 128

class AdocRsc:
    def __init__(self) -> None:
        self.addr_pointer: int = None
        self.addr_object: int = None
        self.p1: int = None
        self.p2: int = None
        self.p1_scratch_base: int = None
        self.p1_scratch_size: int = None
        self.p2_scratch_base: int = None
        self.p2_scratch_size: int = None

    def alloc(self, cpus_avail: typing.List):
        self.addr_pointer = addr_space.AllocRandom(8, 8)
        self.addr_object = addr_space.AllocRandom(OBJECT_SIZE, 64)
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
        addr_space.Free(self.addr_pointer)
        addr_space.Free(self.addr_object)
        addr_space.Free(self.p1_scratch_base)
        addr_space.Free(self.p2_scratch_base)


class AdocInit(Action):
    def __init__(self, adoc_rsc: AdocRsc, name: str = None) -> None:
        super().__init__(name)
        self.adoc_rsc = adoc_rsc

    def Body(self):
        addr_object = self.adoc_rsc.addr_object
        addr_pointer = self.adoc_rsc.addr_pointer
        self.c_src = f'memset((void*){addr_pointer:#x}, 0, 8);\n'
        self.c_src += f'memset((void*){addr_object:#x}, 0, {OBJECT_SIZE:#x});\n'


class AdocP1(Action):
    def __init__(self, adoc_rsc: AdocRsc, offset: int, name: str = None) -> None:
        super().__init__(name)
        self.adoc_rsc = adoc_rsc
        self.offset = offset
        self.executor_id = adoc_rsc.p1

    def Body(self):

        addr_pointer = self.adoc_rsc.addr_pointer
        addr_object = self.adoc_rsc.addr_object

        func_name = f'{self.name}_asm_func'
        with v8.proc(func_name, rf):
            with v8.gpr_alloc(3) as (r1, r2, r5):
                v8.ldr64_pseudo(r1, addr_object)
                v8.ldr64_pseudo(r2, addr_pointer)
                v8.mov32_imm(r5, 0x55)

                # noise
                v8.comment('noise0')
                for i in range(random.randrange(4, 64)):
                    v8.arithm_imm()
                v8.comment('noise end')

                # sets new data in a field
                v8.verbatim(f'str {r5.v32}, [{r1.v64}, #{self.offset:#x}]')

                # noise
                v8.comment(f'noise1')
                for i in range(random.randrange(0, 8)):
                    v8.arithm_imm()
                v8.comment('noise end')

                # updates base address
                if armv7:
                    v8.str64_imm_post(r1, r2)
                    v8.dmb(v8.DmbOption.ST)
                else:
                    v8.stlr64(r1, r2)

                # noise
                v8.comment('noise2')
                for i in range(random.randrange(4, 20)):
                    v8.arithm_imm()
                v8.comment('noise end')

        self.c_src = f'{self.name}_asm_func();\n'


class AdocP2(Action):
    def __init__(self, adoc_rsc: AdocRsc, offset: int, name: str = None) -> None:
        super().__init__(name)
        self.adoc_rsc = adoc_rsc
        self.offset = offset
        self.executor_id = adoc_rsc.p2

    def Body(self):
        r1_r, r2_r, r5_r = random.sample(v8.GPRS, 3)
        x1 = v8.reg64(r1_r)
        x2 = v8.reg64(r2_r)
        w5 = v8.reg32(r5_r)

        addr_pointer = self.adoc_rsc.addr_pointer
        addr_object = self.adoc_rsc.addr_object

        func_name = f'{self.name}_asm_func'
        with v8.proc(func_name, rf):
            with v8.gpr_alloc(3) as (r1, r2, r5):
                v8.ldr64_pseudo(r2, addr_pointer)

                # wait(base_address != nullptr)
                v8.label('1')
                v8.ldr64_imm_post(r1, r2)
                v8.cmp64_imm(r1, 0)
                v8.beq('1b')

                v8.comment('noise0')
                for i in range(random.randrange(0, 8)):
                    v8.arithm_imm()
                v8.verbatim('// noise end')

                v8.verbatim(f'ldr {r5.v32}, [{r1.v64}, #{self.offset:#x}]')

                # checking
                v8.cmp32_imm(r5, 0x55)
                v8.beq('1f')
                v8.mov64_imm(v8.Reg.R0, 1)
                v8.verbatim('bl xrt_exit')
                v8.label('1')

        self.c_src = f'{self.name}_asm_func();\n'


class AdocOver(Action):
    def __init__(self, name: str = None) -> None:
        super().__init__(name)

    def Body(self):
        self.c_src = f'// adoc over\n'


class Adoc(Action):
    def __init__(self, adoc_rsc: AdocRsc, name: str = None) -> None:
        super().__init__(name)
        self.adoc_rsc = adoc_rsc

    def Activity(self):
        Do(AdocInit(self.adoc_rsc))
        offset = random.randrange(0, OBJECT_SIZE)
        offset = offset & ((1 << 64) - 1 - 3)
        with Parallel():
            Do(AdocP1(self.adoc_rsc, offset))
            Do(AdocP2(self.adoc_rsc, offset))
        Do(AdocOver())


class Entry(Action):
    def __init__(self, iters: int = 2, name: str = None) -> None:
        super().__init__(name)
        self.iters = iters
        self.c_headers = ['#include <linux/compiler.h>',
                          '#include <ivy/print.h>']

    def Activity(self):
        for i in range(self.iters):
            cpus = [i for i in range(nr_cpus)]
            adoc_rsc = AdocRsc()
            adoc_rsc.alloc(cpus)
            Do(Adoc(adoc_rsc))
            adoc_rsc.free()
