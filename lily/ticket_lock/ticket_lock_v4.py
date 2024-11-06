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
from purslane.aarch64 import v8
from purslane.aarch64 import locks

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
            r1 = v8.Reg.R1
            # counter address register
            ca_r = v8.Reg.R2
            # keep two address registers

            for ii in range(INCR_TIMES):
                cnt_r = v8.Reg.R3

                # v8.verbatim(f'ldr {r1}, ={addr_lock:#x}')
                v8.ldr64_pseudo(r1, addr_lock)

                if isinstance(addr_counter, int):
                    # v8.verbatim(f'ldr {ca}, ={addr_counter:#x}')
                    v8.ldr64_pseudo(ca_r, addr_counter)
                else:
                    v8.ldr64_pseudo(ca_r, addr_counter)
                    v8.ldr64_imm_post(ca_r, ca_r)
                    # v8.verbatim(f'ldr {ca}, ={addr_counter}')
                    # v8.verbatim(f'ldr {ca}, [{ca}]')

                locks.ticket_lock_acq_excl_r32(v8.Reg.R1, v8.Reg.R5, v8.Reg.R6)
                # lock(v8.Reg.R1, v8.Reg.R5, v8.Reg.R6)

                # increase the counter by 1
                v8.ldr64_imm_post(cnt_r, ca_r)
                v8.add64_imm(cnt_r, cnt_r, 1)
                v8.str64_imm_post(cnt_r, ca_r)

                locks.ticket_unlock_rel_excl_r32(v8.Reg.R1, v8.Reg.R6)
                # unlock(v8.Reg.R1, v8.Reg.R6)

                # do not corrupt the two address registers
                with v8.reserve([r1, ca_r]):
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
