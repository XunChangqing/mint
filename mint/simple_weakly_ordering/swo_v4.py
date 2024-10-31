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
from purslane.aarch64.instr_stream import PushStackStream, PopStackStream, RandLoadStoreStream, SubProc
import vsc
from purslane.aarch64.instr_pkg import Reg, reg_name

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


@vsc.randobj
class WorkerCfg:
    def __init__(self) -> None:
        self.r1 = vsc.rand_enum_t(Reg)
        self.r2 = vsc.rand_enum_t(Reg)
        self.r5 = vsc.rand_enum_t(Reg)
        self.r6 = vsc.rand_enum_t(Reg)
        self.r7 = vsc.rand_enum_t(Reg)
        # TODO
        # number of noise instructions
        # 激励参数的选择，通过覆盖率驱动，机器学习的方法进行训练？
        self.num_noise0 = vsc.rand_bit_t(6)
        self.num_noise1 = vsc.rand_bit_t(6)
        self.num_noise2 = vsc.rand_bit_t(6)

    @vsc.constraint
    def worker_cfg_cons(self):
        vsc.unique(self.r1, self.r2, self.r5, self.r6, self.r7)


class SimpleWeaklyOrderingP1(Action):
    def __init__(self, swo_rsc: SwoRsc, name: str = None) -> None:
        super().__init__(name)
        self.swo_rsc = swo_rsc
        self.executor_id = swo_rsc.p1

    def noise_seq(self, rand_cfg: WorkerCfg, num: int) -> typing.List:
        rls = RandLoadStoreStream()
        rls.page_addr = self.swo_rsc.p1_scratch_base
        rls.page_size = self.swo_rsc.p1_scratch_size
        rls.reserved_rd.extend(
            [rand_cfg.r1, rand_cfg.r2, rand_cfg.r5, rand_cfg.r6])
        rls.randomize()
        return rls.gen_seq(num)

    def Body(self):
        func_name = f'{self.name}_asm_func'
        sub_proc = SubProc(func_name)
        rand_cfg = WorkerCfg()
        rand_cfg.randomize()
        r1 = reg_name(rand_cfg.r1, True)
        r2 = reg_name(rand_cfg.r2, True)
        r5 = reg_name(rand_cfg.r5, True)
        r6 = reg_name(rand_cfg.r6, True)
        r7 = reg_name(rand_cfg.r7, True)
        addr_a = self.swo_rsc.addr_a
        addr_b = self.swo_rsc.addr_b
        addr_c = self.swo_rsc.addr_c

        logger.info(f'p1 {r1} {r2} {r5} {r6}')

        sub_proc.add_inst_s(f'ldr {r1}, ={addr_a:#x}')
        sub_proc.add_inst_s(f'ldr {r2}, ={addr_b:#x}')
        sub_proc.add_inst_s(f'ldr {r5}, ={0x5555555555555555:#x}')
        sub_proc.add_inst_s(f'ldr {r6}, ={0x6666666666666666:#x}')
        # R1 <- addr_a
        # R2 <- addr_b

        # noise, reserve r1, r2, r5, r6
        sub_proc.add_inst_s(f'// noise0 length {rand_cfg.num_noise0}')
        sub_proc.add_seq(self.noise_seq(rand_cfg, rand_cfg.num_noise0))
        sub_proc.add_inst_s('// noise end')

        # STR R5, [R1]
        sub_proc.add_inst_s(f'str {r5}, [{r1}]')

        # noise
        sub_proc.add_inst_s(f'// noise1 length {rand_cfg.num_noise1}')
        sub_proc.add_seq(self.noise_seq(rand_cfg, rand_cfg.num_noise1))
        sub_proc.add_inst_s('// noise end')

        # LDR R6, [R2]
        sub_proc.add_inst_s(f'ldr {r6}, [{r2}]')

        # noise
        sub_proc.add_inst_s(f'// noise2 length {rand_cfg.num_noise2}')
        sub_proc.add_seq(self.noise_seq(rand_cfg, rand_cfg.num_noise2))
        sub_proc.add_inst_s('// noise end')

        # R0 <- addr_c
        # STR R6, [R0] for checking
        sub_proc.add_inst_s(f'ldr {r7}, ={addr_c:#x}')
        sub_proc.add_inst_s(f'str {r6}, [{r7}]')

        sub_proc.writef(rf)

        self.c_src = f'{self.name}_asm_func();\n'


class SimpleWeaklyOrderingP2(Action):
    def __init__(self, swo_rsc: SwoRsc, name: str = None) -> None:
        super().__init__(name)
        self.swo_rsc = swo_rsc
        self.executor_id = swo_rsc.p2

    def noise_seq(self, rand_cfg: WorkerCfg, num: int) -> typing.List:
        rls = RandLoadStoreStream()
        rls.page_addr = self.swo_rsc.p1_scratch_base
        rls.page_size = self.swo_rsc.p1_scratch_size
        rls.reserved_rd.extend(
            [rand_cfg.r1, rand_cfg.r2, rand_cfg.r5, rand_cfg.r6])
        rls.randomize()
        return rls.gen_seq(num)
    
    def Body(self):
        func_name = f'{self.name}_asm_func'
        sub_proc = SubProc(func_name)

        rand_cfg = WorkerCfg()
        rand_cfg.randomize()
        r1 = reg_name(rand_cfg.r1, True)
        r2 = reg_name(rand_cfg.r2, True)
        r5 = reg_name(rand_cfg.r5, True)
        r6 = reg_name(rand_cfg.r6, True)
        r7 = reg_name(rand_cfg.r7, True)

        addr_a = self.swo_rsc.addr_a
        addr_b = self.swo_rsc.addr_b
        addr_d = self.swo_rsc.addr_d

        sub_proc.add_inst_s(f'ldr {r1}, ={addr_a:#x}')
        sub_proc.add_inst_s(f'ldr {r2}, ={addr_b:#x}')
        sub_proc.add_inst_s(f'ldr {r5}, ={0x5555555555555555:#x}')
        sub_proc.add_inst_s(f'ldr {r6}, ={0x6666666666666666:#x}')
        # R1 <- addr_a
        # R2 <- addr_b

        # noise, reserve r1, r2, r5, r6
        sub_proc.add_inst_s(f'// noise0 length {rand_cfg.num_noise0}')
        sub_proc.add_seq(self.noise_seq(rand_cfg, rand_cfg.num_noise0))
        sub_proc.add_inst_s('// noise end')

        # STR R6, [R2]
        sub_proc.add_inst_s(f'str {r6}, [{r2}]')

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

        # R0 <- addr_c
        # STR R6, [R0] for checking
        sub_proc.add_inst_s(f'ldr {r7}, ={addr_d:#x}')
        sub_proc.add_inst_s(f'str {r5}, [{r7}]')

        sub_proc.writef(rf)

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
