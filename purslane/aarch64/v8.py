# author : zuoqian
# Copyright 2024. All rights reserved.
import logging
import sys
import random
import typing
from enum import Enum, IntEnum, auto

logger = logging.getLogger('aarch64.v8')


class Imm(IntEnum):
    IMM = 0  # signed immediate
    UIMM = auto()  # unsigned immediate
    NZUIMM = auto()  # non-zero unsigned immediate
    NZIMM = auto()  # non-zero signed immediate

    # ZERO = 0 # 31
    # SP = auto() # 31


class Reg(IntEnum):
    R0 = auto()
    R1 = auto()
    R2 = auto()
    R3 = auto()
    R4 = auto()
    R5 = auto()
    R6 = auto()
    R7 = auto()
    R8 = auto()
    R9 = auto()
    R10 = auto()
    R11 = auto()
    R12 = auto()
    R13 = auto()
    R14 = auto()
    R15 = auto()
    R16 = auto()
    R17 = auto()
    R18 = auto()
    R19 = auto()
    R20 = auto()
    R21 = auto()
    R22 = auto()
    R23 = auto()
    R24 = auto()
    R25 = auto()
    R26 = auto()
    R27 = auto()
    R28 = auto()
    R29 = auto()
    R30 = auto()
    ZERO = auto()
    SP = auto()

    @property
    def v32(self) -> str:
        return reg_name(self, False)

    @property
    def v64(self) -> str:
        return reg_name(self, True)


GPRS = [Reg.R0, Reg.R1, Reg.R2, Reg.R3, Reg.R4, Reg.R5, Reg.R6, Reg.R7, Reg.R8, Reg.R9,
        Reg.R10, Reg.R11, Reg.R12, Reg.R13, Reg.R14, Reg.R15, Reg.R16, Reg.R17, Reg.R18, Reg.R19,
        Reg.R20, Reg.R21, Reg.R22, Reg.R23, Reg.R24, Reg.R25, Reg.R26, Reg.R27, Reg.R28, Reg.R29, Reg.R30]


def reg_name(r: Reg, v64: bool) -> str:
    if v64:
        match r:
            case Reg.ZERO:
                return 'xzr'
            case Reg.SP:
                return 'sp'
            case _:
                return r.name.replace('R', 'x')
    else:
        match r:
            case Reg.ZERO:
                return 'wzr'
            case Reg.SP:
                return 'wsp'
            case _:
                return r.name.replace('R', 'w')


def reg64(r: Reg) -> str:
    return reg_name(r, True)


def reg32(r: Reg) -> str:
    return reg_name(r, False)


class ShiftType(IntEnum):
    LSL = 0
    LSR = auto()
    ASR = auto()


ALL_SHIFT_TYPE = [ShiftType.LSL, ShiftType.LSR, ShiftType.ASR]


class ExtendType(IntEnum):
    UXTB = 0
    UXTH = auto()
    UXTW = auto()
    UXTX = auto()
    SXTB = auto()
    SXTH = auto()
    SXTW = auto()
    SXTX = auto()


class InstrCategory(IntEnum):
    LOAD = 0
    STORE = auto()
    SHIFT = auto()
    ARITHMETIC = auto()
    LOGICAL = auto()


class Mnemonic(IntEnum):
    ADD = 0
    ADDS = auto()
    SUB = auto()
    SUBS = auto()
    CMP = auto()
    CMN = auto()
    NEG = auto()
    NEGS = auto()


ALL_MNEMONIC = [Mnemonic.ADD, Mnemonic.ADDS, Mnemonic.SUB,
                Mnemonic.SUBS, Mnemonic.CMP, Mnemonic.CMN, Mnemonic.NEG, Mnemonic.NEGS]

# @vsc.randobj


class ArithmeticImm:
    def __init__(self) -> None:
        self.variant_64bit: bool = None
        self.rd: Reg = None
        self.rn: Reg = None
        self.imm: int = None
        self.is_add: bool = None
        self.signed: bool = None
        self.shift: bool = None

        # self.variant_64bit = vsc.rand_bit_t(1)
        # self.rd = vsc.rand_enum_t(Reg)
        # self.rn = vsc.rand_enum_t(Reg)
        # self.imm = vsc.rand_bit_t(12)
        # self.is_add = vsc.rand_bit_t(1)
        # self.signed = vsc.rand_bit_t(1)
        # self.shift = vsc.rand_bit_t(1)

    def randomize_with(self, reserved_regs: typing.List[Reg]):
        self.variant_64bit = bool(random.getrandbits(1))
        self.imm = random.getrandbits(12)
        self.is_add = bool(random.getrandbits(1))
        self.signed = bool(random.getrandbits(1))
        self.shift = bool(random.getrandbits(1))
        all_regs = GPRS[:]
        self.rn = random.choice(all_regs)
        allowed_regs = []
        for r in all_regs:
            if r not in reserved_regs:
                allowed_regs.append(r)
        self.rd = random.choice(allowed_regs)

        # if self.rd in reserved_regs:
        #     logger.critical('failed')
        #     sys.exit(1)

    # @vsc.constraint
    # def arithmetic_imm_cons(self):
        # self.rn != Reg.ZERO

        # with vsc.if_then(self.signed):
        #     self.rd != Reg.SP
        # with vsc.else_then():
        #     self.rd != Reg.ZERO

    def convert2asm(self):
        ret = ''

        if self.is_add:
            ret = 'add'
        else:
            ret = 'sub'

        if self.signed:
            ret += 's'

        ret += f' {reg_name(self.rd, self.variant_64bit)}'
        ret += f' ,{reg_name(self.rn, self.variant_64bit)}'
        ret += f', #{self.imm:#x}'
        if self.shift:
            ret += ',LSL #12'

        return ret


# @vsc.randobj
class ArithmeticShiftedRegister:
    def __init__(self) -> None:
        # self.variant_64bit = vsc.rand_bit_t(1)
        # self.rd = vsc.rand_enum_t(Reg)
        # self.rn = vsc.rand_enum_t(Reg)
        # self.rm = vsc.rand_enum_t(Reg)
        # self.mnemonic = vsc.rand_enum_t(Mnemonic)
        # self.shift_type = vsc.rand_enum_t(instr_pkg.ShiftType)
        # self.amount = vsc.rand_bit_t(6)

        self.variant_64bit: bool = None
        self.rd: Reg = None
        self.rn: Reg = None
        self.rm: Reg = None
        self.mnemonic: Mnemonic = None
        self.shift_type: ShiftType = None
        self.amount: int = None

    # @vsc.constraint
    # def arithmetic_shifted_registers_cons(self):
    #     # self.rm != Reg.ZERO
    #     # self.rm != Reg.SP
    #     # self.rd != Reg.SP
    #     # self.rd != Reg.ZERO
    #     # self.rn != Reg.SP
    #     # self.rn != Reg.ZERO
    #     self.mnemonic in vsc.rangelist(Mnemonic.ADD, Mnemonic.ADDS, Mnemonic.SUB,
    #                                    Mnemonic.SUBS, Mnemonic.CMN, Mnemonic.CMP, Mnemonic.NEG, Mnemonic.NEGS)
    #     self.shift_type in vsc.rangelist(
    #         ShiftType.LSL, ShiftType.LSR, ShiftType.ASR)

    def randomize_with(self, reserved_regs: typing.List[Reg]):
        self.variant_64bit = bool(random.getrandbits(1))
        all_regs = GPRS[:]
        allowed_regs = []
        for r in all_regs:
            if r not in reserved_regs:
                allowed_regs.append(r)
        self.rd = random.choice(allowed_regs)
        self.rn = random.choice(all_regs)
        self.rm = random.choice(all_regs)
        self.mnemonic = random.choice([Mnemonic.ADD,
                                       Mnemonic.ADDS,
                                       Mnemonic.SUB,
                                       Mnemonic.SUBS,
                                       Mnemonic.CMP,
                                       Mnemonic.CMN,
                                       Mnemonic.NEG,
                                       Mnemonic.NEGS])
        self.shift_type = random.choice(
            [ShiftType.LSL, ShiftType.LSR, ShiftType.ASR])
        self.amount = random.getrandbits(6)

    def convert2asm(self):
        ret = f'{self.mnemonic.name}'
        first_reg = True
        if self.mnemonic == Mnemonic.CMN or self.mnemonic == Mnemonic.CMP:
            pass
        else:
            ret += f' {reg_name(self.rd, self.variant_64bit)}'
            first_reg = False

        if self.mnemonic == Mnemonic.NEG or self.mnemonic == Mnemonic.NEGS:
            pass
        else:
            if first_reg:
                first_reg = False
            else:
                ret += ', '
            ret += f' {reg_name(self.rn, self.variant_64bit)}'

        ret += f', {reg_name(self.rm, self.variant_64bit)}'
        ret += f', {self.shift_type.name}'
        amount = self.amount
        if not self.variant_64bit:
            amount = amount & 0x1F
        ret += f' #{amount:#x}'
        return ret

# loads and stores
# load/store immediate


# @vsc.randobj
# class LdStImm:
#     # LDR(LDRW) LDRB(w), LDRH(w), LDRSB, LDRSH, LDRSW

#     def __init__(self) -> None:
#         # support post_index with unscaled offset only
#         self.post_index = True
#         self.pre_index = False
#         self.unsigned_offset = True

#         # self.variant_64bit = vsc.rand_bit_t(1)
#         self.rt = vsc.rand_enum_t(instr_pkg.Reg)
#         self.rn = vsc.rand_enum_t(instr_pkg.Reg)
#         # self.simm = vsc.rand_int_t(9)
#         self.pimm = vsc.rand_bit_t(12)
#         self.data_size = vsc.rand_bit_t(4)
#         self.is_load = vsc.rand_bit_t(1)
#         self.is_signed = vsc.rand_bit_t(1)
#         self.target_64bit = vsc.rand_bit_t(1)

#     @vsc.constraint
#     def ld_st_imm_cons(self):
#         # self.rt != instr_pkg.Reg.SP
#         # self.rt != instr_pkg.Reg.ZERO
#         # self.rn != instr_pkg.Reg.ZERO
#         self.rt != self.rn
#         self.data_size in vsc.rangelist(1, 2, 4, 8)
#         with vsc.if_then(self.is_load):
#             with vsc.if_then(self.is_signed):
#                 self.data_size != 8
#                 # signed extension
#                 with vsc.if_then(self.data_size == 4):
#                     # word can only be extended to 64bit
#                     self.target_64bit == 1
#             with vsc.else_then():
#                 # no signed extension
#                 with vsc.if_then(self.data_size == 8):
#                     self.target_64bit == 1
#                 with vsc.else_then():
#                     self.target_64bit == 0
#         with vsc.else_then():
#             with vsc.if_then(self.data_size == 8):
#                 self.target_64bit == 1
#             with vsc.else_then():
#                 self.target_64bit == 0

#     def convert2asm(self) -> str:
#         ret = ''
#         if bool(self.is_load):
#             ret = 'ldr'
#         else:
#             ret = 'str'

#         if bool(self.is_load) and bool(self.is_signed):
#             ret += 's'

#         match self.data_size:
#             case 8:
#                 pass
#             case 4:
#                 if bool(self.is_load) and bool(self.is_signed):
#                     ret += 'w'
#             case 2:
#                 ret += 'h'
#             case 1:
#                 ret += 'b'

#         ret += f' {instr_pkg.reg_name(self.rt, self.target_64bit)}'
#         ret += f', [{instr_pkg.reg_name(self.rn, True)}'
#         ret += f', #{self.pimm*self.data_size}]'

#         return ret

# load/store register

# logger.info('after ldrimm')

# class LdrReg(LdrImm):
#     def __init__(self):
#         super().__init__()

# logger.info('after ldrreg')

class proc:
    def __init__(self, name, f=None) -> None:
        self.name = name
        self.f = f
        self.inst_seq = []

    def __enter__(self):
        logger.debug(f'proc enter {self}')
        global global_context
        assert (global_context.current_proc is None)
        global_context.current_proc = self
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        logger.debug(f'proc exit {self}')
        global global_context
        assert (global_context.current_proc is self)
        global_context.current_proc = None

        save_seq = []
        restore_seq = []

        save_seq.append(VerbatimInst('stp x29, x30, [sp, #-16]'))
        save_seq.append(VerbatimInst('stp x19, x20, [sp, #-32]'))
        save_seq.append(VerbatimInst('stp x21, x22, [sp, #-48]'))
        save_seq.append(VerbatimInst('stp x23, x24, [sp, #-64]'))
        save_seq.append(VerbatimInst('stp x25, x26, [sp, #-80]'))
        save_seq.append(VerbatimInst('stp x27, x28, [sp, #-96]'))

        restore_seq.append(VerbatimInst('ldp x29, x30, [sp, #-16]'))
        restore_seq.append(VerbatimInst('ldp x19, x20, [sp, #-32]'))
        restore_seq.append(VerbatimInst('ldp x21, x22, [sp, #-48]'))
        restore_seq.append(VerbatimInst('ldp x23, x24, [sp, #-64]'))
        restore_seq.append(VerbatimInst('ldp x25, x26, [sp, #-80]'))
        restore_seq.append(VerbatimInst('ldp x27, x28, [sp, #-96]'))

        self.inst_seq = save_seq+self.inst_seq+restore_seq

        if self.f is not None:
            self.f.write(f'.pushsection .text.{self.name}, "ax"\n')
            self.f.write(f'ENTRY({self.name})\n')

            for inst in self.inst_seq:
                if isinstance(inst, Label):
                    self.f.write(f'{inst.name}:\n')
                elif isinstance(inst, Comment):
                    self.f.write(f'//{inst.content}\n')
                else:
                    self.f.write(f'\t{inst.convert2asm()}\n')

            self.f.write('\tret\n')
            self.f.write(f'ENDPROC({self.name})\n\n')

    def add_inst(self, inst):
        self.inst_seq.append(inst)


class Context:
    def __init__(self) -> None:
        self.current_proc = None
        self.reserve_list = []
        self.gpr_pool = GPRS[:]

    def reserved_regs(self) -> typing.List[Reg]:
        ret: typing.List[Reg] = []
        for rl in self.reserve_list:
            for r in rl.regs:
                if r not in ret:
                    ret.append(r)

        # reserve allocated registers
        for r in GPRS:
            if r not in self.gpr_pool and r not in ret:
                ret.append(r)
        return ret

    def alloc_gpr(self, n: int = 1) -> typing.List[Reg]:
        assert (len(self.gpr_pool) >= n)
        ret = random.sample(self.gpr_pool, n)
        for r in ret:
            self.gpr_pool.remove(r)
        return ret

    def alloc_gpr_spec(self, *argv):
        for arg in argv:
            print(arg)
            assert (isinstance(arg, Reg))
            assert (arg in self.gpr_pool)
            self.gpr_pool.remove(arg)

    def free_gpr(self, gprs: typing.List[Reg]):
        for arg in gprs:
            assert (isinstance(arg, Reg))
            assert (arg not in self.gpr_pool)
            self.gpr_pool.append(arg)


global_context = Context()


class reserve:
    def __init__(self, regs: typing.List[Reg]) -> None:
        self.regs = regs
        for r in regs:
            assert (isinstance(r, Reg))

    def __enter__(self):
        global global_context
        global_context.reserve_list.append(self)

    def __exit__(self, exc_type, exc_value, traceback):
        global global_context
        tail = global_context.reserve_list[-1]
        assert (tail is self)
        global_context.reserve_list.pop()


class gpr_alloc:
    # allocate n general purpose registers
    def __init__(self, n: int = 1) -> None:
        self.gprs = None
        self.n = n

    def __enter__(self) -> typing.List[Reg]:
        global global_context
        self.gprs = global_context.alloc_gpr(self.n)
        return self.gprs

    def __exit__(self, exc_type, exc_value, traceback):
        global global_context
        global_context.free_gpr(self.gprs)


class gpr_spec:
    def __init__(self, *argv) -> None:
        self.gprs = argv

    def __enter__(self):
        global global_context
        global_context.alloc_gpr_spec(*self.gprs)

    def __exit__(self, exc_type, exc_value, traceback):
        global global_context
        global_context.free_gpr(self.gprs)


class VerbatimInst:
    def __init__(self, inst_str: str = None) -> None:
        self.inst_str = inst_str

    def convert2asm(self):
        return self.inst_str


class Comment:
    def __init__(self, c: str) -> None:
        self.content = c


class Label:
    def __init__(self, name: str) -> None:
        self.name = name


class Cbnz64:
    def __init__(self, rn: Reg, l: str) -> None:
        self.rn = rn
        self.target = l

    def convert2asm(self):
        return f'cbnz {self.rn.v64}, {self.target}'


class Cbnz32:
    def __init__(self, rn: Reg, l: str) -> None:
        self.rn = rn
        self.target = l

    def convert2asm(self):
        return f'cbnz {self.rn.v32}, {self.target}'


class Cbz64:
    def __init__(self, rn: Reg, l: str) -> None:
        self.rn = rn
        self.target = l

    def convert2asm(self):
        return f'cbz {self.rn.v64}, {self.target}'


class Cbz32:
    def __init__(self, rn: Reg, l: str) -> None:
        self.rn = rn
        self.target = l

    def convert2asm(self):
        return f'cbz {self.rn.v32}, {self.target}'


class Bne:
    def __init__(self, l: str) -> None:
        self.target = l

    def convert2asm(self):
        return f'bne {self.target}'


class Beq:
    def __init__(self, l: str) -> None:
        self.target = l

    def convert2asm(self):
        return f'beq {self.target}'


class Add64Imm:
    def __init__(self, rd: Reg, rn: Reg, imm12: int) -> None:
        self.rd = rd
        self.rn = rn
        self.imm12 = imm12

    def convert2asm(self):
        return f'add {self.rd.v64}, {self.rn.v64}, #{self.imm12:#x}'


class Add32Imm:
    def __init__(self, rd: Reg, rn: Reg, imm12: int) -> None:
        self.rd = rd
        self.rn = rn
        self.imm12 = imm12

    def convert2asm(self):
        return f'add {self.rd.v32}, {self.rn.v32}, #{self.imm12:#x}'


class Sub64Imm:
    def __init__(self, rd: Reg, rn: Reg, imm12: int) -> None:
        self.rd = rd
        self.rn = rn
        self.imm12 = imm12

    def convert2asm(self):
        return f'sub {self.rd.v64}, {self.rn.v64}, #{self.imm12:#x}'


class Sub32Imm:
    def __init__(self, rd: Reg, rn: Reg, imm12: int) -> None:
        self.rd = rd
        self.rn = rn
        self.imm12 = imm12

    def convert2asm(self):
        return f'sub {self.rd.v32}, {self.rn.v32}, #{self.imm12:#x}'


class Add64Reg:
    def __init__(self, rd: Reg, rn: Reg, rm: Reg) -> None:
        self.rd = rd
        self.rn = rn
        self.rm = rm

    def convert2asm(self):
        return f'add {self.rd.v64}, {self.rn.v64}, {self.rm.v64}'


class Add32Reg:
    def __init__(self, rd: Reg, rn: Reg, rm: Reg) -> None:
        self.rd = rd
        self.rn = rn
        self.rm = rm

    def convert2asm(self):
        return f'add {self.rd.v32}, {self.rn.v32}, {self.rm.v32}'


class And64Imm:
    def __init__(self, rd: Reg, rn: Reg, imm12: int) -> None:
        self.rd = rd
        self.rn = rn
        self.imm12 = imm12

    def convert2asm(self):
        return f'and {self.rd.v64}, {self.rn.v64}, #{self.imm12:#x}'


class And32Imm:
    def __init__(self, rd: Reg, rn: Reg, imm12: int) -> None:
        self.rd = rd
        self.rn = rn
        self.imm12 = imm12

    def convert2asm(self):
        return f'and {self.rd.v32}, {self.rn.v32}, #{self.imm12:#x}'


class And64Reg:
    def __init__(self, rd: Reg, rn: Reg, rm: Reg) -> None:
        self.rd = rd
        self.rn = rn
        self.rm = rm

    def convert2asm(self):
        return f'and {self.rd.v64}, {self.rn.v64}, {self.rm.v64}'


class And32Reg:
    def __init__(self, rd: Reg, rn: Reg, rm: Reg) -> None:
        self.rd = rd
        self.rn = rn
        self.rm = rm

    def convert2asm(self):
        return f'and {self.rd.v32}, {self.rn.v32}, {self.rm.v32}'


class Cmp64Imm:
    def __init__(self, rn: Reg, imm12: int) -> None:
        self.rn = rn
        self.imm12 = imm12

    def convert2asm(self):
        return f'cmp {self.rn.v64}, #{self.imm12:#x}'


class Cmp32Imm:
    def __init__(self, rn: Reg, imm12: int) -> None:
        self.rn = rn
        self.imm12 = imm12

    def convert2asm(self):
        return f'cmp {self.rn.v32}, #{self.imm12:#x}'


class Cmp64Reg:
    def __init__(self, rn: Reg, rm: Reg, sft: ShiftType, sft_amt: int) -> None:
        self.rn = rn
        self.rm = rm
        self.sft = sft
        self.sft_amt = sft_amt

    def convert2asm(self):
        return f'cmp {self.rn.v64}, {self.rm.v64}, {self.sft.name} #{self.sft_amt}'


class Cmp32Reg:
    def __init__(self, rn: Reg, rm: Reg, sft: ShiftType, sft_amt: int) -> None:
        self.rn = rn
        self.rm = rm
        self.sft = sft
        self.sft_amt = sft_amt

    def convert2asm(self):
        return f'cmp {self.rn.v32}, {self.rm.v32}, {self.sft.name} #{self.sft_amt}'


class Mov64Imm:
    def __init__(self, rd: Reg, imm: int) -> None:
        self.rd = rd
        self.imm = imm

    def convert2asm(self):
        rd_name = reg_name(self.rd, True)
        return f'mov {rd_name}, #{self.imm:#x}'


class Mov32Imm:
    def __init__(self, rd: Reg, imm: int) -> None:
        self.rd = rd
        self.imm = imm

    def convert2asm(self):
        rd_name = reg_name(self.rd, False)
        return f'mov {rd_name}, #{self.imm:#x}'


class PrfmImm:
    def __init__(self, xn: Reg, imm: int = 0) -> None:
        self.xn = xn
        self.imm = imm

    def convert2asm(self) -> str:
        rn_name = reg_name(self.xn, True)
        return f'prfm [{rn_name}, #{self.imm:#x}]'


class Ldr64Pseudo:
    def __init__(self, rt: Reg, imm: int) -> None:
        self.rt = rt
        self.imm = imm

    def convert2asm(self) -> str:
        rt_name = reg_name(self.rt, True)
        if isinstance(self.imm, int):
            return f'ldr {rt_name}, ={self.imm:#x}'
        else:
            return f'ldr {rt_name}, ={self.imm}'


class Ldr32Pseudo:
    def __init__(self, rt: Reg, imm: int) -> None:
        self.rt = rt
        self.imm = imm

    def convert2asm(self) -> str:
        rt_name = reg_name(self.rt, False)
        if isinstance(self.imm):
            return f'ldr {rt_name}, ={self.imm:#x}'
        else:
            return f'ldr {rt_name}, ={self.imm}'


class Ldp64Post:
    def __init__(self, rt1: Reg, rt2: Reg, rn: Reg, imm7: int) -> None:
        self.rt1 = rt1
        self.rt2 = rt2
        self.rn = rn
        self.imm7 = imm7

    def convert2asm(self) -> str:
        return f'ldp {self.rt1.v64}, {self.rt2.v64}, [{self.rn.v64}], #{self.imm7:#x}'


class Ldp32Post:
    def __init__(self, rt1: Reg, rt2: Reg, rn: Reg, imm7: int) -> None:
        self.rt1 = rt1
        self.rt2 = rt2
        self.rn = rn
        self.imm7 = imm7

    def convert2asm(self) -> str:
        return f'ldp {self.rt1.v32}, {self.rt2.v32}, [{self.rn.v64}], #{self.imm7:#x}'


class Ldr64ImmPost:
    def __init__(self, rt: Reg, rn: Reg, imm9: int) -> None:
        self.rt = rt
        self.rn = rn
        assert (isinstance(self.rt, Reg))
        assert (isinstance(self.rn, Reg))
        self.imm9 = imm9
        assert (self.imm9 % 4 == 0)

    def convert2asm(self) -> str:
        rt_name = reg_name(self.rt, True)
        rn_name = reg_name(self.rn, True)
        return f'ldr {rt_name}, [{rn_name}], #{self.imm9:#x}'


class Ldr32ImmPost:
    def __init__(self, rt: Reg, rn: Reg, imm9: int) -> None:
        self.rt = rt
        self.rn = rn
        self.imm9 = imm9

    def convert2asm(self) -> str:
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'ldr {rt_name}, [{rn_name}], #{self.imm9:#x}'


class LdrhImmPost:
    def __init__(self, rt: Reg, rn: Reg, imm9: int) -> None:
        self.rt = rt
        self.rn = rn
        self.imm9 = imm9

    def convert2asm(self) -> str:
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'ldrh {rt_name}, [{rn_name}], #{self.imm9:#x}'


class LdrbImmPost:
    def __init__(self, rt: Reg, rn: Reg, imm9: int) -> None:
        self.rt = rt
        self.rn = rn
        self.imm9 = imm9

    def convert2asm(self) -> str:
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'ldrb {rt_name}, [{rn_name}], #{self.imm9:#x}'


class LdrswImmPost:
    def __init__(self, rt: Reg, rn: Reg, imm9: int) -> None:
        self.rt = rt
        self.rn = rn
        self.imm9 = imm9

    def convert2asm(self) -> str:
        rt_name = reg_name(self.rt, True)
        rn_name = reg_name(self.rn, True)
        return f'ldrsw {rt_name}, [{rn_name}], #{self.imm9:#x}'


class LdrshImmPost:
    def __init__(self, rt: Reg, rn: Reg, imm9: int) -> None:
        self.rt = rt
        self.rn = rn
        self.imm9 = imm9

    def convert2asm(self) -> str:
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'ldrsh {rt_name}, [{rn_name}], #{self.imm9:#x}'


class LdrsbImmPost:
    def __init__(self, rt: Reg, rn: Reg, imm9: int) -> None:
        self.rt = rt
        self.rn = rn
        self.imm9 = imm9

    def convert2asm(self) -> str:
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'ldrsb {rt_name}, [{rn_name}], #{self.imm9:#x}'


class Str64ImmPost:
    def __init__(self, rt: Reg, rn: Reg, imm9: int) -> None:
        self.rt = rt
        self.rn = rn
        self.imm9 = imm9

    def convert2asm(self):
        rt_name = reg_name(self.rt, True)
        rn_name = reg_name(self.rn, True)
        return f'str {rt_name}, [{rn_name}], #{self.imm9:#x}'


class Str32ImmPost:
    def __init__(self, rt: Reg, rn: Reg, imm9: int) -> None:
        self.rt = rt
        self.rn = rn
        self.imm9 = imm9

    def convert2asm(self):
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'str {rt_name}, [{rn_name}], #{self.imm9:#x}'


class StrhImmPost:
    def __init__(self, rt: Reg, rn: Reg, imm9: int) -> None:
        self.rt = rt
        self.rn = rn
        self.imm9 = imm9

    def convert2asm(self):
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'strh {rt_name}, [{rn_name}], #{self.imm9:#x}'


class StrbImmPost:
    def __init__(self, rt: Reg, rn: Reg, imm9: int) -> None:
        self.rt = rt
        self.rn = rn
        self.imm9 = imm9

    def convert2asm(self):
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'strb {rt_name}, [{rn_name}], #{self.imm9:#x}'

# class Ldr64ImmPre:
#     def __init__(self) -> None:
#         pass
# class Ldr64ImmUnscale:
#     def __init__(self) -> None:
#         pass
# class Str64ImmPre
# class Str64ImmUnscale


class Ldaxp64:
    def __init__(self, rt1: Reg, rt2: Reg, rn: Reg) -> None:
        self.rt1 = rt1
        self.rt2 = rt2
        self.rn = rn

    def convert2asm(self) -> str:
        return f'ldaxp {self.rt1.v64}, {self.rt2.v64}, [{self.rn.v64}]'


class Ldaxp32:
    def __init__(self, rt1: Reg, rt2: Reg, rn: Reg) -> None:
        self.rt1 = rt1
        self.rt2 = rt2
        self.rn = rn

    def convert2asm(self) -> str:
        return f'ldaxp {self.rt1.v32}, {self.rt2.v32}, [{self.rn.v64}]'


class Ldaxr64:
    def __init__(self, rt: Reg, rn: Reg) -> None:
        self.rt = rt
        self.rn = rn

    def convert2asm(self) -> str:
        return f'ldaxr {self.rt.v64}, [{self.rn.v64}]'


class Ldaxr32:
    def __init__(self, rt: Reg, rn: Reg) -> None:
        self.rt = rt
        self.rn = rn

    def convert2asm(self) -> str:
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'ldaxr {rt_name}, [{rn_name}]'


class Ldaxrh:
    def __init__(self, rt: Reg, rn: Reg) -> None:
        self.rt = rt
        self.rn = rn

    def convert2asm(self) -> str:
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'ldaxrh {rt_name}, [{rn_name}]'


class Ldaxrb:
    def __init__(self, rt: Reg, rn: Reg) -> None:
        self.rt = rt
        self.rn = rn

    def convert2asm(self) -> str:
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'ldaxrb {rt_name}, [{rn_name}]'


class Stlxp64:
    def __init__(self, rs: Reg, rt1: Reg, rt2: Reg, rn: Reg) -> None:
        self.rs = rs
        self.rt1 = rt1
        self.rt2 = rt2
        self.rn = rn

    def convert2asm(self) -> str:
        return f'stlxp {self.rs.v32}, {self.rt1.v64}, {self.rt2.v64}, [{self.rn.v64}]'


class Stlxp32:
    def __init__(self, rs: Reg, rt1: Reg, rt2: Reg, rn: Reg) -> None:
        self.rs = rs
        self.rt1 = rt1
        self.rt2 = rt2
        self.rn = rn

    def convert2asm(self) -> str:
        return f'stlxp {self.rs.v32}, {self.rt1.v32}, {self.rt2.v32}, [{self.rn.v64}]'


class Stlxr64:
    def __init__(self, rs: Reg, rt: Reg, rn: Reg) -> None:
        self.rs = rs
        self.rt = rt
        self.rn = rn

    def convert2asm(self) -> str:
        rs_name = reg_name(self.rs, False)
        rt_name = reg_name(self.rt, True)
        rn_name = reg_name(self.rn, True)
        return f'stlxr {rs_name}, {rt_name}, [{rn_name}]'


class Stlxr32:
    def __init__(self, rs: Reg, rt: Reg, rn: Reg) -> None:
        self.rs = rs
        self.rt = rt
        self.rn = rn

    def convert2asm(self) -> str:
        rs_name = reg_name(self.rs, False)
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'stlxr {rs_name}, {rt_name}, [{rn_name}]'


class Stlxrh:
    def __init__(self, rs: Reg, rt: Reg, rn: Reg) -> None:
        self.rs = rs
        self.rt = rt
        self.rn = rn

    def convert2asm(self) -> str:
        rs_name = reg_name(self.rs, False)
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'stlxrh {rs_name}, {rt_name}, [{rn_name}]'


class Stlxrb:
    def __init__(self, rs: Reg, rt: Reg, rn: Reg) -> None:
        self.rs = rs
        self.rt = rt
        self.rn = rn

    def convert2asm(self) -> str:
        rs_name = reg_name(self.rs, False)
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'stlxrb {rs_name}, {rt_name}, [{rn_name}]'

# ldar/stlr


class Ldap64:
    def __init__(self, rt1: Reg, rt2: Reg, rn: Reg) -> None:
        self.rt1 = rt1
        self.rt2 = rt2
        self.rn = rn

    def convert2asm(self) -> str:
        return f'ldap {self.rt1.v64}, {self.rt2.v64}, {self.rn.v64}'


class Ldap32:
    def __init__(self, rt1: Reg, rt2: Reg, rn: Reg) -> None:
        self.rt1 = rt1
        self.rt2 = rt2
        self.rn = rn

    def convert2asm(self) -> str:
        return f'ldap {self.rt1.v32}, {self.rt2.v32}, {self.rn.v64}'


class Ldar64:
    def __init__(self, rt: Reg, rn: Reg) -> None:
        self.rt = rt
        self.rn = rn

    def convert2asm(self):
        rt_name = reg_name(self.rt, True)
        rn_name = reg_name(self.rn, True)
        return f'ldar {rt_name}, [{rn_name}]'


class Ldar32:
    def __init__(self, rt: Reg, rn: Reg) -> None:
        self.rt = rt
        self.rn = rn

    def convert2asm(self):
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'ldar {rt_name}, [{rn_name}]'


class Ldarh:
    def __init__(self, rt: Reg, rn: Reg) -> None:
        self.rt = rt
        self.rn = rn

    def convert2asm(self):
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'ldarh {rt_name}, [{rn_name}]'


class Ldarb:
    def __init__(self, rt: Reg, rn: Reg) -> None:
        self.rt = rt
        self.rn = rn

    def convert2asm(self):
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'ldarb {rt_name}, [{rn_name}]'


class Stlp64:
    def __init__(self, rt1: Reg, rt2: Reg, rn: Reg) -> None:
        self.rt1 = rt1
        self.rt2 = rt2
        self.rn = rn

    def convert2asm(self) -> str:
        return f'stlp {self.rt1.v64}, {self.rt2.v64}, [{self.rn.v64}]'


class Stlp32:
    def __init__(self, rt1: Reg, rt2: Reg, rn: Reg) -> None:
        self.rt1 = rt1
        self.rt2 = rt2
        self.rn = rn

    def convert2asm(self) -> str:
        return f'stlp {self.rt1.v32}, {self.rt2.v32}, [{self.rn.v64}]'


class Stlr64:
    def __init__(self, rt: Reg, rn: Reg) -> None:
        self.rt = rt
        self.rn = rn

    def convert2asm(self) -> str:
        rt_name = reg_name(self.rt, True)
        rn_name = reg_name(self.rn, True)
        return f'stlr {rt_name}, [{rn_name}]'


class Stlr32:
    def __init__(self, rt: Reg, rn: Reg) -> None:
        self.rt = rt
        self.rn = rn

    def convert2asm(self) -> str:
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'stlr {rt_name}, [{rn_name}]'


class Stlrh:
    def __init__(self, rt: Reg, rn: Reg) -> None:
        self.rt = rt
        self.rn = rn

    def convert2asm(self) -> str:
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'stlrh {rt_name}, [{rn_name}]'


class Stlrb:
    def __init__(self, rt: Reg, rn: Reg) -> None:
        self.rt = rt
        self.rn = rn

    def convert2asm(self) -> str:
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'stlrb {rt_name}, [{rn_name}]'

# ldxr/stxr


class Ldxp64:
    def __init__(self, rt1: Reg, rt2: Reg, rn: Reg) -> None:
        self.rt1 = rt1
        self.rt2 = rt2
        self.rn = rn

    def convert2asm(self) -> str:
        return f'ldxp {self.rt1.v64}, {self.rt2.v64}, [{self.rn.v64}]'


class Ldxp32:
    def __init__(self, rt1: Reg, rt2: Reg, rn: Reg) -> None:
        self.rt1 = rt1
        self.rt2 = rt2
        self.rn = rn

    def convert2asm(self) -> str:
        return f'ldxp {self.rt1.v32}, {self.rt2.v32}, [{self.rn.v64}]'


class Ldxr64:
    def __init__(self, rt: Reg, rn: Reg) -> None:
        self.rt = rt
        self.rn = rn

    def convert2asm(self) -> str:
        rt_name = reg_name(self.rt, True)
        rn_name = reg_name(self.rn, True)
        return f'ldxr {rt_name}, [{rn_name}]'


class Ldxr32:
    def __init__(self, rt: Reg, rn: Reg) -> None:
        self.rt = rt
        self.rn = rn

    def convert2asm(self) -> str:
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'ldxr {rt_name}, [{rn_name}]'


class Ldxrh:
    def __init__(self, rt: Reg, rn: Reg) -> None:
        self.rt = rt
        self.rn = rn

    def convert2asm(self) -> str:
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'ldxrh {rt_name}, [{rn_name}]'


class Ldxrb:
    def __init__(self, rt: Reg, rn: Reg) -> None:
        self.rt = rt
        self.rn = rn

    def convert2asm(self) -> str:
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'ldxrb {rt_name}, [{rn_name}]'


class Stxp64:
    def __init__(self, rs: Reg, rt1: Reg, rt2: Reg, rn: Reg) -> None:
        self.rs = rs
        self.rt1 = rt1
        self.rt2 = rt2
        self.rn = rn

    def convert2asm(self) -> str:
        return f'stxp {self.rs.v32}, {self.rt1.v64}, {self.rt2.v64}, [{self.rn.v64}]'


class Stxp32:
    def __init__(self, rs: Reg, rt1: Reg, rt2: Reg, rn: Reg) -> None:
        self.rs = rs
        self.rt1 = rt1
        self.rt2 = rt2
        self.rn = rn

    def convert2asm(self) -> str:
        return f'stxp {self.rs.v32}, {self.rt1.v32}, {self.rt2.v32}, [{self.rn.v64}]'


class Stxr64:
    def __init__(self, rs: Reg, rt: Reg, rn: Reg) -> None:
        self.rs = rs
        self.rt = rt
        self.rn = rn

    def convert2asm(self) -> str:
        rs_name = reg_name(self.rs, False)
        rt_name = reg_name(self.rt, True)
        rn_name = reg_name(self.rn, True)
        return f'stxr {rs_name}, {rt_name}, [{rn_name}]'


class Stxr32:
    def __init__(self, rs: Reg, rt: Reg, rn: Reg) -> None:
        self.rs = rs
        self.rt = rt
        self.rn = rn

    def convert2asm(self) -> str:
        rs_name = reg_name(self.rs, False)
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'stxr {rs_name}, {rt_name}, [{rn_name}]'


class Stxrh:
    def __init__(self, rs: Reg, rt: Reg, rn: Reg) -> None:
        self.rs = rs
        self.rt = rt
        self.rn = rn

    def convert2asm(self) -> str:
        rs_name = reg_name(self.rs, False)
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'stxrh {rs_name}, {rt_name}, [{rn_name}]'


class Stxrb:
    def __init__(self, rs: Reg, rt: Reg, rn: Reg) -> None:
        self.rs = rs
        self.rt = rt
        self.rn = rn

    def convert2asm(self) -> str:
        rs_name = reg_name(self.rs, False)
        rt_name = reg_name(self.rt, False)
        rn_name = reg_name(self.rn, True)
        return f'stxrb {rs_name}, {rt_name}, [{rn_name}]'


class DmbOption(IntEnum):
    SY = 0
    LD = auto()
    ST = auto()

    @property
    def lname(self) -> str:
        return self.name.lower()


class Dmb:
    def __init__(self, opt: DmbOption = DmbOption.SY) -> None:
        self.opt = opt

    def convert2asm(self) -> str:
        if self.opt is None:
            return 'dmb'
        else:
            return f'dmb {self.opt.lname}'


def inst_build_func(func):
    def ff(*argv):
        i = func(*argv)
        global global_context
        current_proc = global_context.current_proc
        assert (current_proc is not None)
        current_proc.add_inst(i)
    return ff


@inst_build_func
def verbatim(inst_str: str) -> VerbatimInst:
    return VerbatimInst(inst_str)


@inst_build_func
def comment(c: str) -> Comment:
    return Comment(c)


@inst_build_func
def label(name: str) -> Label:
    return Label(name)


@inst_build_func
def cbnz64(rn: Reg, l: str) -> Cbnz64:
    return Cbnz64(rn, l)


@inst_build_func
def cbnz32(rn: Reg, l: str) -> Cbnz32:
    return Cbnz32(rn, l)


@inst_build_func
def cbz64(rn: Reg, l: str) -> Cbz64:
    return Cbz64(rn, l)


@inst_build_func
def cbz32(rn: Reg, l: str) -> Cbz32:
    return Cbz32(rn, l)


@inst_build_func
def bne(l: str) -> Bne:
    return Bne(l)


@inst_build_func
def beq(l: str) -> Beq:
    return Beq(l)


@inst_build_func
def add64_imm(rd: Reg, rn: Reg, imm12: int) -> Add64Imm:
    return Add64Imm(rd, rn, imm12)


@inst_build_func
def add32_imm(rd: Reg, rn: Reg, imm12: int) -> Add32Imm:
    return Add32Imm(rd, rn, imm12)


@inst_build_func
def sub64_imm(rd: Reg, rn: Reg, imm12: int) -> Sub64Imm:
    return Sub64Imm(rd, rn, imm12)


@inst_build_func
def sub32_imm(rd: Reg, rn: Reg, imm12: int) -> Sub32Imm:
    return Sub32Imm(rd, rn, imm12)


@inst_build_func
def add64_reg(rd: Reg, rn: Reg, rm: Reg) -> Add64Reg:
    return Add64Reg(rd, rn, rm)


@inst_build_func
def add32_reg(rd: Reg, rn: Reg, rm: Reg) -> Add32Reg:
    return Add32Reg(rd, rn, rm)


@inst_build_func
def and64_imm(rd: Reg, rn: Reg, imm12: int) -> And64Imm:
    return And64Imm(rd, rn, imm12)


@inst_build_func
def and32_imm(rd: Reg, rn: Reg, imm12: int) -> And32Imm:
    return And32Imm(rd, rn, imm12)


@inst_build_func
def and64_reg(rd: Reg, rn: Reg, rm: Reg) -> And64Reg:
    return And64Reg(rd, rn, rm)


@inst_build_func
def and32_reg(rd: Reg, rn: Reg, rm: Reg) -> Add32Reg:
    return And32Reg(rd, rn, rm)


@inst_build_func
def cmp64_imm(rn: Reg, imm12: int) -> Cmp64Imm:
    return Cmp64Imm(rn, imm12)


@inst_build_func
def cmp32_imm(rn: Reg, imm12: int) -> Cmp32Imm:
    return Cmp32Imm(rn, imm12)


@inst_build_func
def cmp64_reg(rn: Reg, rm: Reg, sft: ShiftType = ShiftType.LSL, sft_amt: int = 0) -> Cmp64Reg:
    return Cmp64Reg(rn, rm, sft, sft_amt)


@inst_build_func
def cmp32_reg(rn: Reg, rm: Reg, sft: ShiftType = ShiftType.LSL, sft_amt: int = 0) -> Cmp32Reg:
    return Cmp32Reg(rn, rm, sft, sft_amt)


@inst_build_func
def mov64_imm(rd: Reg, imm: int) -> Mov64Imm:
    return Mov64Imm(rd, imm)


@inst_build_func
def mov32_imm(rd: Reg, imm: int) -> Mov32Imm:
    return Mov32Imm(rd, imm)

# @inst_build_func
# def prfm_imm(rn:Reg, imm:int = 0) -> PrfmImm:
#     return PrfmImm(rn, imm)


@inst_build_func
def ldr64_pseudo(rt: Reg, imm: int) -> Ldr64Pseudo:
    return Ldr64Pseudo(rt, imm)


@inst_build_func
def ldr32_pseudo(rt: Reg, imm: int) -> Ldr32Pseudo:
    return Ldr32Pseudo(rt, imm)


@inst_build_func
def ldp64_post(rt1: Reg, rt2: Reg, rn: Reg, imm7: int = 0) -> Ldp64Post:
    return Ldp64Post(rt1, rt2, rn, imm7)


@inst_build_func
def ldp32_post(rt1: Reg, rt2: Reg, rn: Reg, imm7: int = 0) -> Ldp32Post:
    return Ldp32Post(rt1, rt2, rn, imm7)


@inst_build_func
def ldr64_imm_post(rt: Reg, rn: Reg, imm9: int = 0) -> Ldr64ImmPost:
    return Ldr64ImmPost(rt, rn, imm9)


@inst_build_func
def ldr32_imm_post(rt: Reg, rn: Reg, imm9: int = 0) -> Ldr32ImmPost:
    return Ldr32ImmPost(rt, rn, imm9)


@inst_build_func
def ldrh_imm_post(rt: Reg, rn: Reg, imm9: int = 0) -> LdrhImmPost:
    return LdrhImmPost(rt, rn, imm9)


@inst_build_func
def ldrb_imm_post(rt: Reg, rn: Reg, imm9: int = 0) -> LdrbImmPost:
    return LdrbImmPost(rt, rn, imm9)


@inst_build_func
def ldrsw_imm_post(rt: Reg, rn: Reg, imm9: int = 0) -> LdrswImmPost:
    return LdrswImmPost(rt, rn, imm9)


@inst_build_func
def ldrsh_imm_post(rt: Reg, rn: Reg, imm9: int = 0) -> LdrshImmPost:
    return LdrshImmPost(rt, rn, imm9)


@inst_build_func
def ldrsb_imm_post(rt: Reg, rn: Reg, imm9: int = 0) -> LdrshImmPost:
    return LdrsbImmPost(rt, rn, imm9)


@inst_build_func
def str64_imm_post(rt: Reg, rn: Reg, imm9: int = 0) -> Str64ImmPost:
    return Str64ImmPost(rt, rn, imm9)


@inst_build_func
def str32_imm_post(rt: Reg, rn: Reg, imm9: int = 0) -> Str32ImmPost:
    return Str32ImmPost(rt, rn, imm9)


@inst_build_func
def strh_imm_post(rt: Reg, rn: Reg, imm9: int = 0) -> StrhImmPost:
    return StrhImmPost(rt, rn, imm9)


@inst_build_func
def strb_imm_post(rt: Reg, rn: Reg, imm9: int = 0) -> StrbImmPost:
    return StrbImmPost(rt, rn, imm9)

# ldaxr/stlxr


@inst_build_func
def ldaxp64(rt1: Reg, rt2: Reg, rn: Reg) -> Ldaxp64:
    return Ldaxp64(rt1, rt2, rn)


@inst_build_func
def ldaxp32(rt1: Reg, rt2: Reg, rn: Reg) -> Ldaxp32:
    return Ldaxp32(rt1, rt2, rn)


@inst_build_func
def stlxp64(rs: Reg, rt1: Reg, rt2: Reg, rn: Reg) -> Stlxp64:
    return Stlxp64(rs, rt1, rt2, rn)


@inst_build_func
def stlxp32(rs: Reg, rt1: Reg, rt2: Reg, rn: Reg) -> Stlxp32:
    return Stlxp32(rs, rt1, rt2, rn)


@inst_build_func
def ldaxr64(rt: Reg, rn: Reg) -> Ldaxr64:
    return Ldaxr64(rt, rn)


@inst_build_func
def ldaxr32(rt: Reg, rn: Reg) -> Ldaxr32:
    return Ldaxr32(rt, rn)


@inst_build_func
def ldaxrh(rt: Reg, rn: Reg) -> Ldaxrh:
    return Ldaxrh(rt, rn)


@inst_build_func
def ldaxrb(rt: Reg, rn: Reg) -> Ldaxrb:
    return Ldaxrb(rt, rn)


@inst_build_func
def stlxr64(rs: Reg, rt: Reg, rn: Reg) -> Stlxr64:
    return Stlxr64(rs, rt, rn)


@inst_build_func
def stlxr32(rs: Reg, rt: Reg, rn: Reg) -> Stlxr32:
    return Stlxr32(rs, rt, rn)


@inst_build_func
def stlxrh(rs: Reg, rt: Reg, rn: Reg) -> Stlxrh:
    return Stlxrh(rs, rt, rn)


@inst_build_func
def stlxrb(rs: Reg, rt: Reg, rn: Reg) -> Stlxrb:
    return Stlxrb(rs, rt, rn)

# ldar/stlr


@inst_build_func
def ldap64(rt1: Reg, rt2: Reg, rn: Reg) -> Ldap64:
    return Ldap64(rt1, rt2, rn)


@inst_build_func
def ldap32(rt1: Reg, rt2: Reg, rn: Reg) -> Ldap32:
    return Ldap32(rt1, rt2, rn)


@inst_build_func
def ldar64(rt: Reg, rn: Reg) -> Ldar64:
    return Ldar64(rt, rn)


@inst_build_func
def ldar32(rt: Reg, rn: Reg) -> Ldar32:
    return Ldar32(rt, rn)


@inst_build_func
def ldarh(rt: Reg, rn: Reg) -> Ldarh:
    return Ldarh(rt, rn)


@inst_build_func
def ldarb(rt: Reg, rn: Reg) -> Ldarb:
    return Ldarb(rt, rn)


@inst_build_func
def stlp64(rt1: Reg, rt2: Reg, rn: Reg) -> Stlp64:
    return Stlp64(rt1, rt2, rn)


@inst_build_func
def stlp32(rt1: Reg, rt2: Reg, rn: Reg) -> Stlp32:
    return Stlp32(rt1, rt2, rn)


@inst_build_func
def stlr64(rt: Reg, rn: Reg) -> Stlr64:
    return Stlr64(rt, rn)


@inst_build_func
def stlr32(rt: Reg, rn: Reg) -> Stlr32:
    return Stlr32(rt, rn)


@inst_build_func
def stlrh(rt: Reg, rn: Reg) -> Stlrh:
    return Stlrh(rt, rn)


@inst_build_func
def stlrb(rt: Reg, rn: Reg) -> Stlrb:
    return Stlrb(rt, rn)

# ldxr/stxr


@inst_build_func
def ldxp64(rt1: Reg, rt2: Reg, rn: Reg) -> Ldxp64:
    return Ldxp64(rt1, rt2, rn)


@inst_build_func
def ldxp32(rt1: Reg, rt2: Reg, rn: Reg) -> Ldxp32:
    return Ldxp32(rt1, rt2, rn)


@inst_build_func
def stxp64(rs: Reg, rt1: Reg, rt2: Reg, rn: Reg) -> Stxp64:
    return Stxp64(rs, rt1, rt2, rn)


@inst_build_func
def stxp32(rs: Reg, rt1: Reg, rt2: Reg, rn: Reg) -> Stxp32:
    return Stxp32(rs, rt1, rt2, rn)


@inst_build_func
def ldxr64(rt: Reg, rn: Reg) -> Ldxr64:
    return Ldxr64(rt, rn)


@inst_build_func
def ldxr32(rt: Reg, rn: Reg) -> Ldxr32:
    return Ldxr32(rt, rn)


@inst_build_func
def ldxrh(rt: Reg, rn: Reg) -> Ldxrh:
    return Ldxrh(rt, rn)


@inst_build_func
def ldxrb(rt: Reg, rn: Reg) -> Ldxrb:
    return Ldxrb(rt, rn)


@inst_build_func
def stxr64(rs: Reg, rt: Reg, rn: Reg) -> Stxr64:
    return Stlxr64(rs, rt, rn)


@inst_build_func
def stxr32(rs: Reg, rt: Reg, rn: Reg) -> Stxr32:
    return Stlxr32(rs, rt, rn)


@inst_build_func
def stxrh(rs: Reg, rt: Reg, rn: Reg) -> Stxrh:
    return Stlxrh(rs, rt, rn)


@inst_build_func
def stxrb(rs: Reg, rt: Reg, rn: Reg) -> Stxrb:
    return Stxrb(rs, rt, rn)

# dmb


@inst_build_func
def dmb(opt: DmbOption = DmbOption.SY) -> Dmb:
    return Dmb(opt)


@inst_build_func
def arithm_imm() -> ArithmeticImm:
    global global_context
    reserved_regs = global_context.reserved_regs()
    inst = ArithmeticImm()
    inst.randomize_with(reserved_regs)
    return inst


@inst_build_func
def arithm_shifted_reg():
    global global_context
    reserved_regs = global_context.reserved_regs()
    inst = ArithmeticShiftedRegister()
    inst.randomize_with(reserved_regs)
    return inst
