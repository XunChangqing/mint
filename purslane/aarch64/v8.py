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


ALL_REGS = [Reg.R0, Reg.R1, Reg.R2, Reg.R3, Reg.R4, Reg.R5, Reg.R6, Reg.R7, Reg.R8, Reg.R9,
            Reg.R10, Reg.R11, Reg.R12, Reg.R13, Reg.R14, Reg.R15, Reg.R16, Reg.R17, Reg.R18, Reg.R19,
            Reg.R20, Reg.R21, Reg.R22, Reg.R23, Reg.R24, Reg.R25, Reg.R26, Reg.R27, Reg.R28, Reg.R29, Reg.R30]


def reg_name(r: Reg, v64: bool) -> str:
    if v64:
        match r:
            # case Reg.ZERO:
            #     return 'xzr'
            # case Reg.SP:
            #     return 'sp'
            case _:
                return r.name.replace('R', 'x')
    else:
        match r:
            # case Reg.ZERO:
            #     return 'wzr'
            # case Reg.SP:
            #     return 'wsp'
            case _:
                return r.name.replace('R', 'w')


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
        all_regs = ALL_REGS[:]
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
        all_regs = ALL_REGS[:]
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


class VerbatimInst:
    def __init__(self, inst_str: str = None) -> None:
        self.inst_str = inst_str

    def convert2asm(self):
        return self.inst_str


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
                self.f.write(f'\t{inst.convert2asm()}\n')

            self.f.write('\tret\n')
            self.f.write(f'ENDPROC({self.name})\n\n')

    def add_inst(self, inst):
        self.inst_seq.append(inst)


class Context:
    def __init__(self) -> None:
        self.current_proc = None
        self.reserve_list = []

    def reserved_regs(self) -> typing.List[Reg]:
        ret: typing.List[Reg] = []
        for rl in self.reserve_list:
            for r in rl.regs:
                if r not in ret:
                    ret.append(r)
        return ret


global_context = Context()


class reserve:
    def __init__(self, regs:typing.List[Reg]) -> None:
        self.regs = regs
        for r in regs:
            assert(isinstance(r, Reg))

    def __enter__(self):
        global global_context
        global_context.reserve_list.append(self)

    def __exit__(self, exc_type, exc_value, traceback):
        global global_context
        tail = global_context.reserve_list[-1]
        assert (tail is self)
        global_context.reserve_list.pop()


def verbatim(inst_str: str) -> VerbatimInst:
    global global_context
    current_proc = global_context.current_proc
    assert (current_proc is not None)
    inst = VerbatimInst(inst_str)
    current_proc.add_inst(inst)
    return inst


def arithm_imm() -> ArithmeticImm:
    global global_context
    reserved_regs = global_context.reserved_regs()
    inst = ArithmeticImm()
    inst.randomize_with(reserved_regs)
    global_context.current_proc.add_inst(inst)
    return inst


def arithm_shifted_reg():
    global global_context
    reserved_regs = global_context.reserved_regs()
    inst = ArithmeticShiftedRegister()
    inst.randomize_with(reserved_regs)
    global_context.current_proc.add_inst(inst)
    return inst


def ld_st_imm():
    pass
