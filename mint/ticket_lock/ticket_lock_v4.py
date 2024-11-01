# author : zuoqian
# Copyright 2024. All rights reserved.

import logging
import argparse
import typing
import random
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

logger = logging.getLogger('ticket_lock_v4')

addr_space: AddrSpace = None
nr_cpus: int = None

rf = open('rand_proc.S', 'w')
atexit.register(rf.close)

rf.write('#include <linux/linkage.h>\n')

# pointer variable to the counter
counter_pointer: str = None


class TlRsc:
    def __init__(self) -> None:
        self.addr_counter: int = None
        self.addr_lock: int = None
        self.scratch_base: int = None
        self.scratch_size: int = None

    def alloc(self,):
        self.addr_lock = addr_space.AllocRandom(8, 8)
        if counter_pointer is None:
            self.addr_counter = addr_space.AllocRandom(8, 8)
        else:
            self.addr_counter = counter_pointer
        self.scratch_size = 8192
        self.scratch_base = addr_space.AllocRandom(self.scratch_size, 64)

    def free(self):
        if isinstance(self.addr_counter, int):
            addr_space.Free(self.addr_counter)
        addr_space.Free(self.addr_lock)
        addr_space.Free(self.scratch_base)


class TicketLockInit(Action):
    def __init__(self, tl_rsc: TlRsc, name: str = None) -> None:
        super().__init__(name)
        self.tl_rsc = tl_rsc

    def Body(self):
        addr_counter = self.tl_rsc.addr_counter
        addr_lock = self.tl_rsc.addr_lock
        if isinstance(addr_counter, int):
            self.c_src = f'WRITE_ONCE(*(uint64_t*){addr_counter:#x}, 0);\n'
        else:
            self.c_src = f'WRITE_ONCE(*(uint64_t*){addr_counter}, 0);\n'
        self.c_src += f'WRITE_ONCE(*(uint64_t*){addr_lock:#x}, 0x00000001);\n'


class WorkerCfg:
    def __init__(self) -> None:
        self.r0: v8.Reg = None
        self.r1: v8.Reg = None
        self.r2: v8.Reg = None
        self.r5: v8.Reg = None

        self.num_noise0: int = None
        self.num_noise1: int = None
        self.num_noise2: int = None

    def randomize(self):
        rs = random.sample(v8.ALL_REGS, 4)
        self.r0 = rs[0]
        self.r1 = rs[1]
        self.r2 = rs[2]
        self.r3 = rs[3]

        # TODO
        # number of noise instructions
        # 激励参数的选择，通过覆盖率驱动，机器学习的方法进行训练？
        self.num_noise0 = random.getrandbits(6)
        self.num_noise1 = random.getrandbits(6)
        self.num_noise2 = random.getrandbits(6)


def lock(x1_r: v8.Reg, w5_r: v8.Reg, w6_r: v8.Reg):
    x1 = v8.reg_name(x1_r, True)
    w5 = v8.reg_name(w5_r, False)
    w6 = v8.reg_name(w6_r, False)
    v8.verbatim(f'prfm pstl1keep, [{x1}]')
    v8.verbatim(f'1:')
    v8.verbatim(f'ldaxr {w5}, [{x1}]')
    v8.verbatim(f'add {w5}, {w5}, #0x10000')
    v8.verbatim(f'stxr {w6}, {w5}, [{x1}]')
    v8.verbatim(f'cbnz {w6}, 1b')
    v8.verbatim(f'and {w6}, {w5}, 0xFFFF')
    v8.verbatim(f'cmp {w6}, {w5}, LSR #16')
    v8.verbatim(f'beq 3f')
    v8.verbatim(f'2:')
    v8.verbatim(f'ldarh {w6}, [{x1}]')
    v8.verbatim(f'cmp {w6}, {w5}, LSR #16')
    v8.verbatim(f'bne 2b')
    v8.verbatim(f'3:')


def unlock(x1_r: v8.Reg, w6_r: v8.Reg):
    x1 = v8.reg_name(x1_r, True)
    w6 = v8.reg_name(w6_r, False)
    v8.verbatim(f'add {w6}, {w6}, #1')
    v8.verbatim(f'stlrh {w6}, [{x1}]')


INCR_TIMES = 128


class TicketLockIncr(Action):
    def __init__(self, incr_func: str, core_id: int, name: str = None) -> None:
        super().__init__(name)
        self.incr_func = incr_func
        self.executor_id = core_id

    def Body(self):
        self.c_src = f'{self.incr_func}();\n'


class TicketLockCheck(Action):
    def __init__(self, tl_rsc: TlRsc, name: str = None) -> None:
        super().__init__(name)
        self.tl_rsc = tl_rsc

    def Body(self):
        if isinstance(self.tl_rsc.addr_counter, int):
            self.c_src = f'tl_check((uint64_t*){self.tl_rsc.addr_counter:#x}, {nr_cpus*INCR_TIMES});\n'
        else:
            self.c_src = f'tl_check((uint64_t*){self.tl_rsc.addr_counter}, {nr_cpus*INCR_TIMES});\n'


class TicketLockTest(Action):
    def __init__(self, tl_rsc: TlRsc, name: str = None) -> None:
        super().__init__(name)
        self.tl_rsc = tl_rsc

    def gen_incr_func(self) -> str:
        addr_counter = self.tl_rsc.addr_counter
        addr_lock = self.tl_rsc.addr_lock
        func_name = f'{self.name}_asm_incr_func'
        with v8.proc(func_name, rf):
            # lock address register
            r1_r = v8.Reg.R1
            # counter address register
            ca_r = v8.Reg.R2
            r1 = v8.reg_name(r1_r, True)
            ca = v8.reg_name(ca_r, True)
            # keep two address registers

            for ii in range(INCR_TIMES):
                ca_tmp_r = v8.Reg.R3
                ca_tmp = v8.reg_name(ca_tmp_r, True)

                v8.verbatim(f'ldr {r1}, ={addr_lock:#x}')
                if isinstance(addr_counter, int):
                    v8.verbatim(f'ldr {ca}, ={addr_counter:#x}')
                else:
                    v8.verbatim(f'ldr {ca}, ={addr_counter}')
                    v8.verbatim(f'ldr {ca}, [{ca}]')

                lock(v8.Reg.R1, v8.Reg.R5, v8.Reg.R6)

                # increase the counter by 1
                v8.verbatim(f'ldr {ca_tmp}, [{ca}]')
                v8.verbatim(f'add {ca_tmp}, {ca_tmp}, #1')
                v8.verbatim(f'str {ca_tmp}, [{ca}]')

                unlock(v8.Reg.R1, v8.Reg.R6)

                # do not corrupt the two address registers
                with v8.reserve([r1_r, ca_r]):
                    for jj in range(random.randrange(4, 20)):
                        v8.arithm_imm()
        return func_name

    def Activity(self):
        Do(TicketLockInit(self.tl_rsc))
        # all cores share the same code increasing the counter
        # otherwise the generated code would be huge, especially when the number of cores is big
        func_name = self.gen_incr_func()
        with Parallel():
            for i in range(nr_cpus):
                Do(TicketLockIncr(func_name, i))
        Do(TicketLockCheck(self.tl_rsc))


class Entry(Action):
    def __init__(self, iters: int = 2, name: str = None) -> None:
        super().__init__(name)
        self.iters = iters
        self.c_headers = ['#include <linux/compiler.h>',
                          '#include <ivy/print.h>', '#include "cfunc.h"']

    def Activity(self):
        for i in range(self.iters):
            logger.info(f'ticket lock iter {i}')
            tl_rsc = TlRsc()
            tl_rsc.alloc()
            Do(TicketLockTest(tl_rsc))
            tl_rsc.free()
