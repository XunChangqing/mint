# author : zuoqian
# Copyright 2024. All rights reserved.

import logging
import argparse
import typing
import random
import math
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
from purslane.aarch64.instr_stream import PushStackStream, PopStackStream, RandLoadStoreStream, SubProc, random_delay, RandDataProcessingStream
import vsc
from purslane.aarch64.instr_pkg import Reg, reg_name
from purslane.aarch64.isa.v8 import VerbatimInst, VerbatimInstScope

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
        if self.addr_counter is int:
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
        self.c_src = f'WRITE_ONCE(*(uint64_t*){addr_counter}, 0);\n'
        self.c_src += f'WRITE_ONCE(*(uint64_t*){addr_lock}, 0x00000001);\n'


@vsc.randobj
class WorkerCfg:
    def __init__(self) -> None:
        self.r0 = vsc.rand_enum_t(Reg)
        self.r1 = vsc.rand_enum_t(Reg)
        self.r2 = vsc.rand_enum_t(Reg)
        self.r5 = vsc.rand_enum_t(Reg)
        # TODO
        # number of noise instructions
        # 激励参数的选择，通过覆盖率驱动，机器学习的方法进行训练？
        self.num_noise0 = vsc.rand_bit_t(6)
        self.num_noise1 = vsc.rand_bit_t(6)
        self.num_noise2 = vsc.rand_bit_t(6)

    @vsc.constraint
    def worker_cfg_cons(self):
        vsc.unique(self.r0, self.r1, self.r2, self.r5)


def lock(x1_r: Reg, w5_r: Reg, w6_r: Reg) -> typing.List:
    x1 = reg_name(x1_r, True)
    w5 = reg_name(w5_r, False)
    w6 = reg_name(w6_r, False)
    with VerbatimInstScope() as vis:
        VerbatimInst(f'prfm pstl1keep, [{x1}]')
        VerbatimInst(f'1:')
        VerbatimInst(f'ldaxr {w5}, [{x1}]')
        VerbatimInst(f'add {w5}, {w5}, #0x10000')
        VerbatimInst(f'stxr {w6}, {w5}, [{x1}]')
        VerbatimInst(f'cbnz {w6}, 1b')
        VerbatimInst(f'and {w6}, {w5}, 0xFFFF')
        VerbatimInst(f'cmp {w6}, {w5}, LSR #16')
        VerbatimInst(f'beq 3f')
        VerbatimInst(f'2:')
        VerbatimInst(f'ldarh {w6}, [{x1}]')
        VerbatimInst(f'cmp {w6}, {w5}, LSR #16')
        VerbatimInst(f'bne 2b')
        VerbatimInst(f'3:')

    return vis.inst_seq


def unlock(x1_r: Reg, w6_r: Reg) -> typing.List:
    x1 = reg_name(x1_r, True)
    w6 = reg_name(w6_r, False)

    with VerbatimInstScope() as vis:
        VerbatimInst(f'add {w6}, {w6}, #1')
        VerbatimInst(f'stlrh {w6}, [{x1}]')

    return vis.inst_seq


INCR_TIMES = 128


class TicketLockIncr(Action):
    def __init__(self, tl_rsc: TlRsc, core_id: int, name: str = None) -> None:
        super().__init__(name)
        self.tl_rsc = tl_rsc
        self.executor_id = core_id

    # def noise_seq(self, rand_cfg: WorkerCfg, num: int) -> typing.List:
    #     rls = RandLoadStoreStream()
    #     rls.page_addr = self.mp_rsc.p1_scratch_base
    #     rls.page_size = self.mp_rsc.p1_scratch_size
    #     rls.reserved_rd.extend(
    #         [rand_cfg.r0, rand_cfg.r1, rand_cfg.r2, rand_cfg.r5])
    #     rls.randomize()
    #     return rls.gen_seq(num)

    def Body(self):
        func_name = f'{self.name}_asm_func'
        sub_proc = SubProc(func_name)
        # rand_cfg = WorkerCfg()
        # rand_cfg.randomize()
        # r0 = reg_name(rand_cfg.r0, True)
        # r1 = reg_name(rand_cfg.r1, True)
        # r2 = reg_name(rand_cfg.r2, True)
        # r5 = reg_name(rand_cfg.r5, True)
        addr_counter = self.tl_rsc.addr_counter
        addr_lock = self.tl_rsc.addr_lock

        # sub_proc.add_seq(random_delay(Reg.R1, 5, 64))

        for ii in range(INCR_TIMES):
            r1_r = Reg.R1
            # counter address register
            ca_r = Reg.R2
            ca_tmp_r = Reg.R3
            r1 = reg_name(r1_r, True)
            ca = reg_name(ca_r, True)
            ca_tmp = reg_name(ca_tmp_r, True)
            sub_proc.add_inst_s(f'ldr {r1}, ={addr_lock:#x}')
            if addr_counter is int:
                sub_proc.add_inst_s(f'ldr {ca}, ={addr_counter}')
            else:
                sub_proc.add_inst_s(f'ldr {ca}, ={addr_counter}')
                sub_proc.add_inst_s(f'ldr {ca}, [{ca}]')

            sub_proc.add_seq(lock(Reg.R1, Reg.R5, Reg.R6))

            # increase the counter by 1
            sub_proc.add_inst_s(f'ldr {ca_tmp}, [{ca}]')
            sub_proc.add_inst_s(f'add {ca_tmp}, {ca_tmp}, #1')
            sub_proc.add_inst_s(f'str {ca_tmp}, [{ca}]')

            sub_proc.add_seq(unlock(Reg.R1, Reg.R6))

            # 随机数量数据指令，使用 vsc 生成，速度很慢
            # use vsc, very slow
            # rdps = RandDataProcessingStream()
            # rdps.randomize()
            # sub_proc.add_seq(rdps.gen_seq(random.randrange(4, 20)))

            # simply append random number of float insts
            for jj in range(random.randrange(4, 20)):
                sub_proc.add_inst_s(f'fmul d0, d1, d2')

        sub_proc.writef(rf)

        self.c_src = f'{self.name}_asm_func();\n'


class TicketLockCheck(Action):
    def __init__(self, tl_rsc: TlRsc, name: str = None) -> None:
        super().__init__(name)
        self.tl_rsc = tl_rsc

    def Body(self):
        if self.tl_rsc.addr_counter is int:
            self.c_src = f'tl_check((uint64_t*){self.tl_rsc.addr_counter:#x}, {nr_cpus*INCR_TIMES});\n'
        else:
            self.c_src = f'tl_check((uint64_t*){self.tl_rsc.addr_counter}, {nr_cpus*INCR_TIMES});\n'


class TicketLockTest(Action):
    def __init__(self, tl_rsc: TlRsc, name: str = None) -> None:
        super().__init__(name)
        self.tl_rsc = tl_rsc

    def Activity(self):
        Do(TicketLockInit(self.tl_rsc))
        with Parallel():
            for i in range(nr_cpus):
                Do(TicketLockIncr(self.tl_rsc, i))
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
