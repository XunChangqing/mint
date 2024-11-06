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
from purslane.aarch64 import locks
from purslane.aarch64.v8 import Reg

logger = logging.getLogger('lock_counter_v4')

addr_space: AddrSpace = None
nr_cpus: int = None
armv7: bool = False

rf = open('rand_proc.S', 'w')
atexit.register(rf.close)

rf.write('#include <linux/linkage.h>\n')

# 避免生成代码规模膨胀
# 1. 一次迭代中，所有 increase 共享一个实现，通过参数进行随机控制，所有 disturb 也可以共享一个实现
# 2. 整个程序运行中，所有 increase 共享一个实现，通过参数进行随机控制，所有 disturb 也可以共享一个实现
# 都是有代价的，使得不同处理核执行的代码是相同的，但是如果每次代码生成的结果是随机变化的，在单次执行中，不同处理核
# 使用相同代码，与现实环境中 Single Program Multiple Thread 的代码编写方式也有类似之处
# 具体的函数仍然通过 python 生成，而不是直接通过 c/asm hardwired，有以下优势：
# 1. 支持每次生成时代码不同
# 2. 支持每遍迭代不同
# 3. 支持每个处理核不同
# 从平衡上看，
# 1. 代码最小，variation 最小
# 2. 代码中等，variation 中等
# 3. 代码较大，特别是处理核数量较大时


def inc_counter(ca: Reg):
    # ca counter address
    with v8.gpr_alloc(1) as (tr1,):  # comma is needed to unzip the return list
        v8.ldr64_imm_post(tr1, ca)
        v8.add64_imm(tr1, tr1, 1)
        v8.str64_imm_post(tr1, ca)
    # filler


GLOBAL_INC_FUNC_NAME = 'inc_counter_asm_func'
GLOBAL_DISTURB_FUNC_NAME = 'disturb_asm_func'

NUM_LOCK_TYPES = 12

# lock exclusive with acquire-release semantics


def inc_acq_rel_excl_pair64(la: Reg, ca: Reg):
    # la lock address
    # ca counter address
    with v8.gpr_alloc(3) as (tr25, tr27, tr28):
        locks.lock_acq_excl_pair64(la, tr25, tr27, tr28)
        inc_counter(ca)
        locks.unlock_rel_excl_pair64(la, tr25, tr27, tr28)
        # filler


def inc_acq_rel_excl_pair32(la: Reg, ca: Reg):
    with v8.gpr_alloc(3) as (tr25, tr27, tr28):
        locks.lock_acq_excl_pair32(la, tr25, tr27, tr28)
        inc_counter(ca)
        locks.unlock_rel_excl_pair32(la, tr25, tr27, tr28)


def inc_acq_rel_excl_r64(la: Reg, ca: Reg):
    with v8.gpr_alloc(2) as (tr25, tr27):
        locks.lock_acq_excl_r64(la, tr25, tr27)
        inc_counter(ca)
        locks.unlock_rel_excl_r64(la)


def inc_acq_rel_excl_r32(la: Reg, ca: Reg):
    with v8.gpr_alloc(2) as (tr25, tr27):
        locks.lock_acq_excl_r32(la, tr25, tr27)
        inc_counter(ca)
        locks.unlock_rel_excl_r32(la)


def inc_acq_rel_excl_r16(la: Reg, ca: Reg):
    with v8.gpr_alloc(2) as (tr25, tr27):
        locks.lock_acq_excl_r16(la, tr25, tr27)
        inc_counter(ca)
        locks.unlock_rel_excl_r16(la)


def inc_acq_rel_excl_r8(la: Reg, ca: Reg):
    with v8.gpr_alloc(2) as (tr25, tr27):
        locks.lock_acq_excl_r8(la, tr25, tr27)
        inc_counter(ca)
        locks.unlock_rel_excl_r8(la)

# exclusive with dmb


def inc_dmb_excl_pair64(la: Reg, ca: Reg):
    # la lock address
    # ca counter address
    with v8.gpr_alloc(3) as (tr25, tr27, tr28):
        locks.lock_dmb_excl_pair64(la, tr25, tr27, tr28)
        inc_counter(ca)
        locks.unlock_dmb_excl_pair64(la, tr25, tr27, tr28)
        # filler


def inc_dmb_excl_pair32(la: Reg, ca: Reg):
    with v8.gpr_alloc(3) as (tr25, tr27, tr28):
        locks.lock_dmb_excl_pair32(la, tr25, tr27, tr28)
        inc_counter(ca)
        locks.unlock_dmb_excl_pair32(la, tr25, tr27, tr28)


def inc_dmb_excl_r64(la: Reg, ca: Reg):
    with v8.gpr_alloc(2) as (tr25, tr27):
        locks.lock_dmb_excl_r64(la, tr25, tr27)
        inc_counter(ca)
        locks.unlock_dmb_excl_r64(la)


def inc_dmb_excl_r32(la: Reg, ca: Reg):
    with v8.gpr_alloc(2) as (tr25, tr27):
        locks.lock_dmb_excl_r32(la, tr25, tr27)
        inc_counter(ca)
        locks.unlock_dmb_excl_r32(la)


def inc_dmb_excl_r16(la: Reg, ca: Reg):
    with v8.gpr_alloc(2) as (tr25, tr27):
        locks.lock_dmb_excl_r16(la, tr25, tr27)
        inc_counter(ca)
        locks.unlock_dmb_excl_r16(la)


def inc_dmb_excl_r8(la: Reg, ca: Reg):
    with v8.gpr_alloc(2) as (tr25, tr27):
        locks.lock_dmb_excl_r8(la, tr25, tr27)
        inc_counter(ca)
        locks.unlock_dmb_excl_r8(la)


def gen_increase_func(name: str):
    with v8.proc(name, rf):
        with v8.gpr_spec(Reg.R0, Reg.R1, Reg.R2, Reg.R3):
            v8.label('10')
            # x0 lock address
            # x1 counter address
            # x2 times increasing the counter
            # x3 lock type

            v8.cmp64_imm(Reg.R3, 0)
            v8.bne('12f')
            v8.label('11')
            inc_acq_rel_excl_pair64(Reg.R0, Reg.R1)
            v8.verbatim('b 30f')

            v8.cmp64_imm(Reg.R3, 1)
            v8.bne('13f')
            v8.label('12')
            inc_acq_rel_excl_pair32(Reg.R0, Reg.R1)
            v8.verbatim('b 30f')

            v8.cmp64_imm(Reg.R3, 2)
            v8.bne('14f')
            v8.label('13')
            inc_acq_rel_excl_r64(Reg.R0, Reg.R1)
            v8.verbatim('b 30f')

            v8.cmp64_imm(Reg.R3, 3)
            v8.bne('15f')
            v8.label('14')
            inc_acq_rel_excl_r32(Reg.R0, Reg.R1)
            v8.verbatim('b 30f')

            v8.cmp64_imm(Reg.R3, 4)
            v8.bne('16f')
            v8.label('15')
            inc_acq_rel_excl_r16(Reg.R0, Reg.R1)
            v8.verbatim('b 30f')

            v8.cmp64_imm(Reg.R3, 5)
            v8.bne('17f')
            v8.label('16')
            inc_acq_rel_excl_r8(Reg.R0, Reg.R1)
            v8.verbatim('b 30f')

            v8.cmp64_imm(Reg.R3, 6)
            v8.bne('18f')
            v8.label('17')
            inc_dmb_excl_pair64(Reg.R0, Reg.R1)
            v8.verbatim('b 30f')

            v8.cmp64_imm(Reg.R3, 7)
            v8.bne('19f')
            v8.label('18')
            inc_dmb_excl_pair32(Reg.R0, Reg.R1)
            v8.verbatim('b 30f')

            v8.cmp64_imm(Reg.R3, 8)
            v8.bne('20f')
            v8.label('19')
            inc_dmb_excl_r64(Reg.R0, Reg.R1)
            v8.verbatim('b 30f')

            v8.cmp64_imm(Reg.R3, 9)
            v8.bne('21f')
            v8.label('20')
            inc_dmb_excl_r32(Reg.R0, Reg.R1)
            v8.verbatim('b 30f')

            v8.cmp64_imm(Reg.R3, 10)
            v8.bne('22f')
            v8.label('21')
            inc_dmb_excl_r16(Reg.R0, Reg.R1)
            v8.verbatim('b 30f')

            v8.cmp64_imm(Reg.R3, 11)
            v8.bne('23f')
            v8.label('22')
            inc_dmb_excl_r8(Reg.R0, Reg.R1)
            v8.verbatim('b 30f')

            v8.label('23')

            v8.label('30')
            v8.sub64_imm(Reg.R2, Reg.R2, 1)
            v8.cbnz64(Reg.R2, '10b')


def gen_disturb_func(name: str):
    # x0 lock address, random load within 32 bytes
    # x1 stop flag address
    with v8.proc(name, rf):
        with v8.gpr_spec(Reg.R0, Reg.R1):
            with v8.gpr_alloc(3) as (flag_r, tr1, tr2):
                v8.label('10')

                # n random loads
                for i in range(random.randrange(4, 16)):
                    # 1 byte -> 16 bytes
                    data_size = random.randrange(0, 5)
                    data_size = (1 << data_size)
                    offset = random.randrange(0, 32)
                    # round down
                    offset = (offset//data_size)*data_size

                    match data_size:
                        case 1:
                            v8.ldrb_imm_post(tr1, Reg.R0, offset)
                        case 2:
                            v8.ldrh_imm_post(tr1, Reg.R0, offset)
                        case 4:
                            v8.ldr32_imm_post(tr1, Reg.R0, offset)
                        case 8:
                            v8.ldp32_post(tr1, tr2, Reg.R0, offset)
                            v8.ldr64_imm_post(tr1, Reg.R0, offset)
                        case 16:
                            v8.ldp64_post(tr1, tr2, Reg.R0, offset)

                v8.ldr64_imm_post(flag_r, Reg.R1)
                v8.cbz64(flag_r, '10b')


class Sem:
    def __init__(self) -> None:
        self.addr_lock: int = None
        self.addr_counter: int = None
        # total count
        self.count: int = 0
        self.lock_type: int = 0

    def alloc(self):
        self.count = 0
        # all cores accessing the same semaphore should use the same locking method
        self.lock_type = random.randrange(0, NUM_LOCK_TYPES)
        # 最大的 ldp64 锁也只会使用 16 字节
        # 三种 counter 摆放位置可能
        # 1. 与 lock 相邻，距离可以随机
        # 2. 其他随机 mem 位置
        # 3. pcie 设备的寄存器的 address space 中分配
        self.addr_lock = addr_space.AllocRandom(32, 16)
        # 内核中很多时候锁和数据放在同一个结构体呢，所以这里放在一起
        self.addr_counter = self.addr_lock + 16
        # self.addr_counter = addr_space.AllocRandom(8, 8)
        logger.info(
            f'sem lock address: {self.addr_lock:#x}, counter address: {self.addr_counter:#x}, lock type: {self.lock_type}')

    def free(self):
        addr_space.Free(self.addr_lock)
        # addr_space.Free(self.addr_counter)


class Rsc:
    def __init__(self) -> None:
        # n 个 semaphore，可以是随机数量
        self.sems: typing.List[Sem] = []
        self.flag_end_disturb: int = None

    def alloc(self):
        n = random.randrange(1, nr_cpus)
        logger.info(f'number of semaphores {n}')
        for i in range(n):
            s = Sem()
            s.alloc()
            self.sems.append(s)
        self.flag_end_disturb = addr_space.AllocRandom(8, 8)

    def free(self):
        for s in self.sems:
            s.free()
        self.sems.clear()
        addr_space.Free(self.flag_end_disturb)


class Init(Action):
    def __init__(self, rsc: Rsc, name: str = None) -> None:
        super().__init__(name)
        self.rsc = rsc

    def Body(self):
        self.c_src = f'memset((void*){self.rsc.flag_end_disturb:#x}, 0, 8);\n'
        for s in self.rsc.sems:
            assert (s.count == 0)
            addr_lock = s.addr_lock
            addr_counter = s.addr_counter
            self.c_src += f'memset((void*){addr_lock:#x}, 0, 32);\n'
            self.c_src += f'memset((void*){addr_counter:#x}, 0, 8);\n'


class Increase(Action):
    def __init__(self, rsc: Rsc, executor_id: int, name: str = None) -> None:
        super().__init__(name)
        self.rsc = rsc
        self.executor_id = executor_id

    def Body(self):
        sem = random.choice(self.rsc.sems)
        addr_lock = sem.addr_lock
        addr_counter = sem.addr_counter
        cnt_times = random.randrange(10, 120)
        sem.count += cnt_times
        self.c_src = f'{GLOBAL_INC_FUNC_NAME}({addr_lock:#x}, {addr_counter:#x}, {cnt_times}, {sem.lock_type});\n'


class Disturb(Action):
    def __init__(self, rsc: Rsc, ec: int, name: str = None) -> None:
        super().__init__(name)
        self.rsc = rsc
        self.executor_id = ec

    def Body(self):
        # self.c_src = f'{self.name}_asm_func();\n'
        sem = random.choice(self.rsc.sems)
        self.c_src = f'{GLOBAL_DISTURB_FUNC_NAME}({sem.addr_lock:#x}, {self.rsc.flag_end_disturb:#x});\n'


class StopDisturb(Action):
    def __init__(self, rsc: Rsc, ec: int, name: str = None) -> None:
        super().__init__(name)
        self.rsc = rsc
        self.executor_id = ec

    def Body(self):
        self.c_src = f'WRITE_ONCE(*(uint64_t*){self.rsc.flag_end_disturb:#x}, 1);\n'


class Check(Action):
    def __init__(self, rsc: Rsc, name: str = None) -> None:
        super().__init__(name)
        self.rsc = rsc

    def Body(self):
        self.c_src = '//checking\n'
        for s in self.rsc.sems:
            self.c_src += f'check((uint64_t*){s.addr_counter:#x}, {s.count});\n'


class LdstExcl(Action):
    def __init__(self, rsc: Rsc, name: str = None) -> None:
        super().__init__(name)
        self.rsc = rsc

    def Activity(self):
        Do(Init(self.rsc))
        with Parallel():
            cpus = [i for i in range(nr_cpus)]
            random.shuffle(cpus)
            hf = len(cpus)//2
            inc_cpus = cpus[:hf]
            dis_cpus = cpus[hf:]
            with Parallel():
                for dc in dis_cpus:
                    Do(Disturb(self.rsc, dc))
            with Sequence():
                with Parallel():
                    for ic in inc_cpus:
                        Do(Increase(self.rsc, ic))
                # the core stopping the disturbance should be one of the cores doing increasement
                # otherwise it can not run because disturbers occupy the cores and do not release control
                stop_ec = random.choice(inc_cpus)
                Do(StopDisturb(self.rsc, stop_ec))
        Do(Check(self.rsc))


class Entry(Action):
    def __init__(self, iters: int = 2, name: str = None) -> None:
        super().__init__(name)
        self.iters = iters
        self.c_headers = ['#include <linux/compiler.h>',
                          '#include <ivy/print.h>',
                          '#include "check.h"']

    def Activity(self):
        logger.info(
            'generate global increase function shared by all cores for all iterations')
        gen_increase_func(GLOBAL_INC_FUNC_NAME)
        gen_disturb_func(GLOBAL_DISTURB_FUNC_NAME)

        for i in range(self.iters):
            rsc = Rsc()
            rsc.alloc()
            Do(LdstExcl(rsc))
            rsc.free()
