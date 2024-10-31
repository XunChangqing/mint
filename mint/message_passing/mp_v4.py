# author : zuoqian
# Copyright 2024. All rights reserved.

import ivy_app_cfg
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
from purslane.aarch64.instr_stream import PushStackStream, PopStackStream, RandLoadStoreStream, SubProc, random_delay
import vsc
from purslane.aarch64.instr_pkg import Reg, reg_name

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


class MessagePassingP1(Action):
    def __init__(self, mp_rsc: MpRsc, name: str = None) -> None:
        super().__init__(name)
        self.mp_rsc = mp_rsc
        self.executor_id = mp_rsc.p1

    def noise_seq(self, rand_cfg: WorkerCfg, num: int) -> typing.List:
        rls = RandLoadStoreStream()
        rls.page_addr = self.mp_rsc.p1_scratch_base
        rls.page_size = self.mp_rsc.p1_scratch_size
        rls.reserved_rd.extend(
            [rand_cfg.r0, rand_cfg.r1, rand_cfg.r2, rand_cfg.r5])
        rls.randomize()
        return rls.gen_seq(num)

    def Body(self):
        func_name = f'{self.name}_asm_func'
        sub_proc = SubProc(func_name)
        rand_cfg = WorkerCfg()
        rand_cfg.randomize()
        r0 = reg_name(rand_cfg.r0, True)
        r1 = reg_name(rand_cfg.r1, True)
        r2 = reg_name(rand_cfg.r2, True)
        r5 = reg_name(rand_cfg.r5, True)
        addr_data = self.mp_rsc.addr_data
        addr_flag = self.mp_rsc.addr_flag

        sub_proc.add_seq(random_delay(Reg.R1, 5, 64))

        sub_proc.add_inst_s(f'ldr {r1}, ={addr_data:#x}')
        sub_proc.add_inst_s(f'ldr {r2}, ={addr_flag:#x}')
        sub_proc.add_inst_s(f'mov {r5}, #0x55')
        sub_proc.add_inst_s(f'mov {r0}, #1')

        # noise
        sub_proc.add_inst_s(f'// noise0 length {rand_cfg.num_noise0}')
        sub_proc.add_seq(self.noise_seq(rand_cfg, rand_cfg.num_noise0))
        sub_proc.add_inst_s('// noise end')

        # STR R5, [R1] sets new data
        sub_proc.add_inst_s(f'str {r5}, [{r1}]')

        # noise
        sub_proc.add_inst_s(f'// noise1 length {rand_cfg.num_noise1}')
        sub_proc.add_seq(self.noise_seq(rand_cfg, rand_cfg.num_noise1))
        sub_proc.add_inst_s('// noise end')

        # STL R0, [R2] sends flag
        sub_proc.add_inst_s(f'str {r0}, [{r2}]')

        # noise
        sub_proc.add_inst_s(f'// noise2 length {rand_cfg.num_noise2}')
        sub_proc.add_seq(self.noise_seq(rand_cfg, rand_cfg.num_noise2))
        sub_proc.add_inst_s('// noise end')

        sub_proc.writef(rf)

        self.c_src = f'{self.name}_asm_func();\n'


class MessagePassingP2(Action):
    def __init__(self, mp_rsc: MpRsc, name: str = None) -> None:
        super().__init__(name)
        self.mp_rsc = mp_rsc
        self.executor_id = mp_rsc.p2

    def noise_seq(self, rand_cfg: WorkerCfg, num: int) -> typing.List:
        rls = RandLoadStoreStream()
        rls.page_addr = self.mp_rsc.p1_scratch_base
        rls.page_size = self.mp_rsc.p1_scratch_size
        rls.reserved_rd.extend(
            [rand_cfg.r1, rand_cfg.r2, rand_cfg.r5])
        rls.randomize()
        return rls.gen_seq(num)

    def Body(self):
        func_name = f'{self.name}_asm_func'
        sub_proc = SubProc(func_name)

        rand_cfg = WorkerCfg()
        rand_cfg.randomize()
        r0 = reg_name(rand_cfg.r0, True)
        r1 = reg_name(rand_cfg.r1, True)
        r2 = reg_name(rand_cfg.r2, True)
        r5 = reg_name(rand_cfg.r5, True)

        addr_data = self.mp_rsc.addr_data
        addr_flag = self.mp_rsc.addr_flag

        sub_proc.add_inst_s(f'ldr {r1}, ={addr_data:#x}')
        sub_proc.add_inst_s(f'ldr {r2}, ={addr_flag:#x}')

        sub_proc.add_inst_s(f'// noise0 length {rand_cfg.num_noise0}')
        sub_proc.add_seq(self.noise_seq(rand_cfg, rand_cfg.num_noise0))
        sub_proc.add_inst_s('// noise end')

        # WATI_ACQ([R2] == 1)
        # use r0 as the tmp register, it has not to be reserved for noise sequences.
        sub_proc.add_inst_s('1:')
        sub_proc.add_inst_s(f'ldr {r0}, [{r2}]')
        sub_proc.add_inst_s(f'cmp {r0}, #1')
        sub_proc.add_inst_s(f'bne 1b')

        # noise
        sub_proc.add_inst_s(f'// noise1 length {rand_cfg.num_noise1}')
        sub_proc.add_seq(self.noise_seq(rand_cfg, rand_cfg.num_noise1))
        sub_proc.add_inst_s('// noise end')

        # LDR R5, [R1]
        sub_proc.add_inst_s(f'ldr {r5}, [{r1}]')

        # noise
        sub_proc.add_inst_s(f'// noise2 length {rand_cfg.num_noise2}')
        sub_proc.add_seq(self.noise_seq(rand_cfg, rand_cfg.num_noise2))
        sub_proc.add_inst_s('// noise end')

        # checking
        sub_proc.add_inst_s(f'cmp {r5}, #0x55')
        sub_proc.add_inst_s(f'beq 1f')
        sub_proc.add_inst_s(f'mov x0, #1')
        sub_proc.add_inst_s(f'bl xrt_exit')
        sub_proc.add_inst_s(f'1:')

        sub_proc.writef(rf)

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
