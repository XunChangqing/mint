"""
author: zuoqian
Copyright 2024. All rights reserved.
"""

import random
import logging
import typing
import sys
import vsc
import purslane.aarch64.instr_pkg as aarch64_instr_pkg
from purslane.aarch64.isa import v8
from purslane.aarch64.instr_pkg import Reg, reg_name

logger = logging.getLogger('aarch64.instr_stream')

# @vsc.randobj
# class InstrStream:
#     def __init__(self) -> None:
#         self.instr_list = []
#         self.reserved_rd = vsc.list_t(vsc.enum_t(aarch64_instr_pkg.Reg))


@vsc.randobj
class RandDataProcessingStream():
    def __init__(self):
        self.reserved_rd = vsc.list_t(vsc.enum_t(aarch64_instr_pkg.Reg))

    def randomize_gpr(self, inst):
        with inst.randomize_with() as it:
            with vsc.foreach(self.reserved_rd, idx=True) as i:
                inst.rd != self.reserved_rd[i]            
    
    def gen_inst(self):
        inst_list = [v8.ArithmeticImm, v8.ArithmeticShiftedRegister]
        inst_cls = random.choice(inst_list)
        inst = inst_cls()
        self.randomize_gpr(inst)
        return inst
    
    def gen_seq(self, num: int) -> typing.List:
        ret_seq = []
        for i in range(num):
            ret_seq.append(self.gen_inst())
        return ret_seq


@vsc.randobj
class RandLoadStoreStream():
    def __init__(self) -> None:
        self.rn = vsc.rand_enum_t(Reg)
        self.inst_seq = []
        self.reserved_rd = vsc.list_t(vsc.enum_t(Reg))
        self.page_addr = 0
        self.page_size = 4096

    @vsc.constraint
    def rn_cons(self):
        with vsc.foreach(self.reserved_rd, idx=True) as i:
            self.rn != self.reserved_rd[i]

    def mix_seq(self, other_seq: typing.List):
        for other_inst in other_seq:
            pos = random.randrange(0, len(self.inst_seq))
            self.inst_seq.insert(pos, other_inst)

    def gen_inst(self):
        inst = v8.LdStImm()
        with inst.randomize_with() as it:
            it.rn == self.rn
            it.rt != self.rn
            it.pimm*it.data_size + it.data_size < self.page_size
            with vsc.foreach(self.reserved_rd, idx=True) as i:
                it.rt != self.reserved_rd[i]
        return inst

    def gen_seq(self, num:int) -> typing.List:
        if num == 0:
            return []
        logger.info(f'the base register of the load/store stream is {self.rn.name}')
        assert(len(self.inst_seq) == 0)

        if self.rn in self.reserved_rd:
            logger.critical(f'conflict rn {self.rn.name} with reserved rd {self.reserved_rd}')
            sys.exit(1)

        for i in range(num):
            self.inst_seq.append(self.gen_inst())

        ris = RandDataProcessingStream()
        ris.reserved_rd.extend(self.reserved_rd)
        ris.reserved_rd.append(self.rn)
        logger.info(f'{ris.reserved_rd}')
        num_ris = random.randrange(num, num*2)
        ris_seq = ris.gen_seq(num_ris)
        self.mix_seq(ris_seq)

        set_base_inst = v8.VerbatimInst()
        set_base_inst.inst_str = f'ldr {reg_name(self.rn, True)}, ={self.page_addr:#x}'
        self.inst_seq.insert(0,set_base_inst)

        return self.inst_seq
    
    # def post_randomize(self):
    #     if self.rn in self.reserved_rd:
    #         logger.critical(f'post randomize conflict rn {self.rn.name} with reserved rd {self.reserved_rd}')
    #         sys.exit(1)

# class NopStream:
#     def __init__(self, num:int = 8) -> None:
#         self.seq = []

class PushStackStream:
    # r30 LR the link register
    # r29 fp the frame register
    # r19..r28 callee-saved registers
    def __init__(self) -> None:
        pass

    def gen_seq(self) -> typing.List:
        seq = []
        seq.append(v8.VerbatimInst('stp x29, x30, [sp, #-16]'))
        seq.append(v8.VerbatimInst('stp x19, x20, [sp, #-32]'))
        seq.append(v8.VerbatimInst('stp x21, x22, [sp, #-48]'))
        seq.append(v8.VerbatimInst('stp x23, x24, [sp, #-64]'))
        seq.append(v8.VerbatimInst('stp x25, x26, [sp, #-80]'))
        seq.append(v8.VerbatimInst('stp x27, x28, [sp, #-96]'))
        return seq
        

class PopStackStream:
    def __init__(self) -> None:
        pass

    def gen_seq(self) -> typing.List:
        seq = []
        seq.append(v8.VerbatimInst('ldp x29, x30, [sp, #-16]'))
        seq.append(v8.VerbatimInst('ldp x19, x20, [sp, #-32]'))
        seq.append(v8.VerbatimInst('ldp x21, x22, [sp, #-48]'))
        seq.append(v8.VerbatimInst('ldp x23, x24, [sp, #-64]'))
        seq.append(v8.VerbatimInst('ldp x25, x26, [sp, #-80]'))
        seq.append(v8.VerbatimInst('ldp x27, x28, [sp, #-96]'))
        return seq

class SubProc:
    def __init__(self, name: str) -> None:
        self.name = name
        self.inst_seq = []

    def add_inst(self, inst):
        self.inst_seq.append(inst)

    def add_inst_s(self, insts):
        self.inst_seq.append(v8.VerbatimInst(insts))

    def add_seq(self, seq):
        self.inst_seq.extend(seq)

    def writef(self, f):
        f.write(f'.pushsection .text.{self.name}, "ax"\n')
        f.write(f'ENTRY({self.name})\n')
        push_stack_str = PushStackStream()
        seq = push_stack_str.gen_seq()
        for inst in seq:
            f.write(f'\t{inst.convert2asm()}\n')
        
        for inst in self.inst_seq:
            f.write(f'\t{inst.convert2asm()}\n')

        pop_stack_str = PopStackStream()
        seq = pop_stack_str.gen_seq()
        for inst in seq:
            f.write(f'\t{inst.convert2asm()}\n')
        f.write('\tret\n')
        f.write(f'ENDPROC({self.name})\n\n')


def random_delay(reg:Reg, min:int, max:int) -> typing.List:
    assert(min > 0)
    num = random.randrange(min, max)
    inst_seq = []
    r = reg_name(reg, True)
    inst_seq.append(v8.VerbatimInst(f'mov {r}, #{num}'))
    inst_seq.append(v8.VerbatimInst('1:'))
    inst_seq.append(v8.VerbatimInst(f'sub {r}, {r}, #1'))
    inst_seq.append(v8.VerbatimInst(f'cmp {r}, #0'))
    inst_seq.append(v8.VerbatimInst(f'bne 1b'))
    return inst_seq
