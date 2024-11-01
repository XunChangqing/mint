# author : zuoqian
# Copyright 2024. All rights reserved.

import ivy_app_cfg
import logging
import typing
import random
import atexit
from enum import Enum
from purslane.dsl import Do, Action, Sequence, Parallel, Schedule, Select, Run, TypeOverride
from purslane.dsl import RandU8, RandU16, RandU32, RandU64, RandUInt, RandS8, RandS16, RandS32, RandS64, RandInt
from purslane.addr_space import AddrSpace
from purslane.addr_space import SMWrite8, SMWrite16, SMWrite32, SMWrite64, SMWriteBytes
from purslane.addr_space import SMRead8, SMRead16, SMRead32, SMRead64, SMReadBytes
from purslane.aarch64 import v8

# 获取目标平台配置
# import ivy_app_cfg

logger = logging.getLogger('mp_v4')

addr_space: AddrSpace = None
nr_cpus: int = None

rf = open('rand_proc.S', 'w')
atexit.register(rf.close)

rf.write('#include <linux/linkage.h>\n')


class MpRsc:
    def __init__(self) -> None:
        self.addr_data: int = None
        self.addr_flag: int = None
        self.p1: int = None
        self.p2: int = None
        self.p1_scratch_base: int = None
        self.p1_scratch_size: int = None
        self.p2_scratch_base: int = None
        self.p2_scratch_size: int = None

    def alloc(self, cpus_avail: typing.List):
        self.addr_data = addr_space.AllocRandom(8, 8)
        self.addr_flag = addr_space.AllocRandom(8, 8)
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
        addr_space.Free(self.addr_data)
        addr_space.Free(self.addr_flag)
        addr_space.Free(self.p1_scratch_base)
        addr_space.Free(self.p2_scratch_base)


class MessagePassingInit(Action):
    def __init__(self, mp_rsc: MpRsc, name: str = None) -> None:
        super().__init__(name)
        self.mp_rsc = mp_rsc

    def Body(self):
        addr_data = self.mp_rsc.addr_data
        addr_flag = self.mp_rsc.addr_flag
        self.c_src = f'WRITE_ONCE(*(uint64_t*){addr_data}, 0);\n'
        self.c_src += f'WRITE_ONCE(*(uint64_t*){addr_flag}, 0);\n'


class MessagePassingP1(Action):
    def __init__(self, mp_rsc: MpRsc, name: str = None) -> None:
        super().__init__(name)
        self.mp_rsc = mp_rsc
        self.executor_id = mp_rsc.p1

    def Body(self):
        r0_r, r1_r, r2_r, r5_r = random.sample(v8.ALL_REGS, 4)
        r0 = v8.reg_name(r0_r, True)
        r1 = v8.reg_name(r1_r, True)
        r2 = v8.reg_name(r2_r, True)
        r5 = v8.reg_name(r5_r, True)

        addr_data = self.mp_rsc.addr_data
        addr_flag = self.mp_rsc.addr_flag

        func_name = f'{self.name}_asm_func'
        with v8.proc(func_name, rf):
            for i in range(random.randrange(6, 64)):
                v8.verbatim('nop')

            v8.verbatim(f'ldr {r1}, ={addr_data:#x}')
            v8.verbatim(f'ldr {r2}, ={addr_flag:#x}')
            v8.verbatim(f'mov {r5}, #0x55')
            v8.verbatim(f'mov {r0}, #1')

            # noise
            v8.verbatim(f'// noise0')
            with v8.reserve([r0_r, r1_r, r2_r, r5_r]):
                for i in range(random.randrange(4, 64)):
                    v8.arithm_imm()
            v8.verbatim('// noise end')

            # STR R5, [R1] sets new data
            v8.verbatim(f'str {r5}, [{r1}]')

            # noise
            v8.verbatim(f'// noise1')
            with v8.reserve([r0_r, r1_r, r2_r, r5_r]):
                for i in range(random.randrange(0, 8)):
                    v8.arithm_imm()
            v8.verbatim('// noise end')

            # STL R0, [R2] sends flag
            v8.verbatim(f'str {r0}, [{r2}]')

            # noise
            v8.verbatim(f'// noise2')
            with v8.reserve([r0_r, r1_r, r2_r, r5_r]):
                for i in range(random.randrange(4, 20)):
                    v8.arithm_imm()
            v8.verbatim('// noise end')

        self.c_src = f'{self.name}_asm_func();\n'


class MessagePassingP2(Action):
    def __init__(self, mp_rsc: MpRsc, name: str = None) -> None:
        super().__init__(name)
        self.mp_rsc = mp_rsc
        self.executor_id = mp_rsc.p2

    def Body(self):
        r0_r, r1_r, r2_r, r5_r = random.sample(v8.ALL_REGS, 4)
        r0 = v8.reg_name(r0_r, True)
        r1 = v8.reg_name(r1_r, True)
        r2 = v8.reg_name(r2_r, True)
        r5 = v8.reg_name(r5_r, True)

        addr_data = self.mp_rsc.addr_data
        addr_flag = self.mp_rsc.addr_flag

        func_name = f'{self.name}_asm_func'
        with v8.proc(func_name, rf):
            v8.verbatim(f'ldr {r1}, ={addr_data:#x}')
            v8.verbatim(f'ldr {r2}, ={addr_flag:#x}')

            v8.verbatim(f'// noise0')
            with v8.reserve([r0_r, r1_r, r2_r, r5_r]):
                for i in range(random.randrange(4, 64)):
                    v8.arithm_imm()
            v8.verbatim('// noise end')

            # WATI_ACQ([R2] == 1)
            # use r0 as the tmp register, it has not to be reserved for noise sequences.
            v8.verbatim('1:')
            v8.verbatim(f'ldr {r0}, [{r2}]')
            v8.verbatim(f'cmp {r0}, #1')
            v8.verbatim(f'bne 1b')

            # noise
            v8.verbatim(f'// noise1')
            with v8.reserve([r0_r, r1_r, r2_r, r5_r]):
                for i in range(random.randrange(0, 8)):
                    v8.arithm_imm()
            v8.verbatim('// noise end')

            # LDR R5, [R1]
            v8.verbatim(f'ldr {r5}, [{r1}]')

            # noise
            v8.verbatim(f'// noise2')
            with v8.reserve([r0_r, r1_r, r2_r, r5_r]):
                for i in range(random.randrange(4, 20)):
                    v8.arithm_imm()
            v8.verbatim('// noise end')

            # checking
            v8.verbatim(f'cmp {r5}, #0x55')
            v8.verbatim(f'beq 1f')
            v8.verbatim(f'mov x0, #1')
            v8.verbatim(f'bl xrt_exit')
            v8.verbatim(f'1:')

        self.c_src = f'{self.name}_asm_func();\n'


class MessagePassingOver(Action):
    def __init__(self, name: str = None) -> None:
        super().__init__(name)

    def Body(self):
        self.c_src = f'// message passing over\n'


class MessagePassing(Action):
    def __init__(self, mp_rsc: MpRsc, name: str = None) -> None:
        super().__init__(name)
        self.mp_rsc = mp_rsc

    def Activity(self):
        Do(MessagePassingInit(self.mp_rsc))
        with Parallel():
            Do(MessagePassingP1(self.mp_rsc))
            Do(MessagePassingP2(self.mp_rsc))
        Do(MessagePassingOver())


class Entry(Action):
    def __init__(self, iters:int = 2, name: str = None) -> None:
        super().__init__(name)
        self.iters = iters
        self.c_headers = ['#include <linux/compiler.h>', '#include <ivy/print.h>']

    def Activity(self):
        for i in range(self.iters):
            cpus = [i for i in range(nr_cpus)]
            mp_rsc = MpRsc()
            mp_rsc.alloc(cpus)
            Do(MessagePassing(mp_rsc))
            mp_rsc.free()
