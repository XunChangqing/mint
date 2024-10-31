import logging

import typing
from enum import Enum, IntEnum, auto
import vsc.rand_obj
from purslane.aarch64.isa.instr import Instr as AArch64Instr
from purslane.aarch64 import instr_pkg
from purslane.aarch64.instr_pkg import Reg, Mnemonic, ShiftType
import vsc

logger = logging.getLogger('aarch64.isa.v8')

# class ArithmeticImm(AArch64Instr):
#     def __init__(self):
#         super().__init__()
#         self.has_rm = False
#         self.has_extend = False
#         self.imm_width = 12

#     @vsc.constraint
#     def shift_amount(self):
#         self.amount == 0 or self.amount == 12
#         self.shift_type == instr_pkg.ShiftType.LSL

#     @vsc.constraint
#     def rd_rn_zero(self):
#         self.rd != instr_pkg.Reg.ZERO
#         self.rn != instr_pkg.Reg.ZERO

# @InstrClass
# class AddImm(ArithmeticImm):
#     def __init__(self):
#         super().__init__()
#         self.mnemonic = 'add'

# @InstrClass
# class AddsImm(ArithmeticImm):
#     def __init__(self):
#         super().__init__()
#         self.mnemonic = 'adds'

#     @vsc.constraint
#     def rd_sp(self):
#         self.rd != instr_pkg.Reg.SP

# @InstrClass
# class SubImm(ArithmeticImm):
#     def __init__(self):
#         super().__init__()
#         self.mnemonic = 'sub'

# @InstrClass
# class SubsImm(ArithmeticImm):
#     def __init__(self):
#         super().__init__()
#         self.mnemonic = 'subs'

#     @vsc.constraint
#     def rd_sp(self):
#         self.rd != instr_pkg.Reg.SP

# @InstrClass
# class CmpImm(ArithmeticImm):
#     def __init__(self):
#         super().__init__()
#         self.mnemonic = 'cmp'
#         self.has_rd = False

# @InstrClass
# class CmnImm(ArithmeticImm):
#     def __init__(self):
#         super().__init__()
#         self.mnemonic = 'cmn'
#         self.has_rd = False

# # class LogicalImm(AArch64Instr):
# #     def __init__(self):
# #         super().__init__()
# #         self.has_rm = False
# #         self.has_extend = False
# #         self.has_shift = False
# #         self.use_bitmask_imm = True

# #     @vsc.constraint
# #     def rd_rn_zero(self):
# #         self.rd != instr_pkg.Reg.ZERO
# #         self.rn != instr_pkg.Reg.ZERO

# # @InstrClass
# # class AndImm(LogicalImm):
# #     def __init__(self):
# #         super().__init__()
# #         self.mnemonic = 'and'

# #     @vsc.constraint
# #     def rn_sp(self):
# #         self.rn != instr_pkg.Reg.SP

# # @InstrClass
# # class AndsImm(LogicalImm):
# #     def __init__(self):
# #         super().__init__()
# #         self.mnemonic = 'ands'

# #     @vsc.constraint
# #     def rn_rd_sp(self):
# #         self.rn != instr_pkg.Reg.SP
# #         self.rd != instr_pkg.Reg.SP

# # @InstrClass
# # class EorImm(LogicalImm):
# #     def __init__(self):
# #         super().__init__()
# #         self.mnemonic = 'eor'

# #     @vsc.constraint
# #     def rn_sp(self):
# #         self.rn != instr_pkg.Reg.SP

# # @InstrClass
# # class OrrImm(LogicalImm):
# #     def __init__(self):
# #         super().__init__()
# #         self.mnemonic = 'orr'

# #     @vsc.constraint
# #     def rn_sp(self):
# #         self.rn != instr_pkg.Reg.SP

# # @InstrClass
# # class TstImm(LogicalImm):
# #     def __init__(self):
# #         super().__init__()
# #         self.mnemonic = 'tst'
# #         self.has_rd = False

# #     @vsc.constraint
# #     def rn_sp(self):
# #         self.rn != instr_pkg.Reg.SP

# class MoveWideImm(AArch64Instr):
#     def __init__(self):
#         super().__init__()
#         self.has_rn = False
#         self.has_rm = False
#         self.has_extend = False
#         self.imm_width = 16

#     @vsc.constraint
#     def shift_rd(self):
#         self.rd != instr_pkg.Reg.SP
#         self.rd != instr_pkg.Reg.ZERO
#         self.shift_type == instr_pkg.ShiftType.LSL
#         with vsc.if_then(self.variant_64bit):
#             self.amount in vsc.rangelist(0, 16, 32, 48)
#         with vsc.else_then():
#             self.amount in vsc.rangelist(0, 16)

# @InstrClass
# class MovkImm(MoveWideImm):
#     def __init__(self):
#         super().__init__()
#         self.mnemonic = 'movk'

# @InstrClass
# class MovnImm(MoveWideImm):
#     def __init__(self):
#         super().__init__()
#         self.mnemonic = 'movn'

# @InstrClass
# class MovzImm(MoveWideImm):
#     def __init__(self):
#         super().__init__()
#         self.mnemonic = 'movz'

# # @InstrClass
# # class MovInvertedWideImm(MovnImm):
# #     def __init__(self):
# #         super().__init__()
# #         self.mnemonic = 'mov'
# #         self.has_shift = False

# # @InstrClass
# # class MovWideImm(MovzImm):
# #     def __init__(self):
# #         super().__init__()
# #         self.mnemonic = 'mov'
# #         self.has_shift = False

# # @InstrClass
# # class MovBitmaskImm(MoveWideImm):
# #     def __init__(self):
# #         super().__init__()

# #         self.has_shift = False
# #         self.use_bitmask_imm = True

# # 需要label
# # ADRP
# # ADR

# # data processing register
# class ArithShiftedReg(AArch64Instr):
#     def __init__(self):
#         super().__init__()
#         self.has_extend = False
#         self.has_imm = False

#     @vsc.constraint
#     def reg_ops(self):
#         self.rn != instr_pkg.Reg.SP
#         self.rn != instr_pkg.Reg.ZERO
#         self.rm != instr_pkg.Reg.SP
#         self.rm != instr_pkg.Reg.ZERO
#         self.rd != instr_pkg.Reg.SP
#         self.rd != instr_pkg.Reg.ZERO

#     def post_randomize(self):
#         if bool(self.variant_64bit):
#             self.amount_width = 6
#         else:
#             self.amount_width = 5
#         super().post_randomize()

# @InstrClass
# class AddShiftedReg(ArithShiftedReg):
#     def __init__(self):
#         super().__init__()
#         self.mnemonic = 'add'

# @InstrClass
# class AddsShiftedReg(ArithShiftedReg):
#     def __init__(self):
#         super().__init__()
#         self.mnemonic = 'adds'

# @InstrClass
# class SubShiftedReg(ArithShiftedReg):
#     def __init__(self):
#         super().__init__()
#         self.mnemonic = 'sub'

# @InstrClass
# class SubsShiftedReg(ArithShiftedReg):
#     def __init__(self):
#         super().__init__()
#         self.mnemonic = 'subs'

# @InstrClass
# class CmnShiftedReg(ArithShiftedReg):
#     def __init__(self):
#         super().__init__()
#         self.has_rd = False
#         self.mnemonic = 'cmn'

# @InstrClass
# class CmpShiftedReg(ArithShiftedReg):
#     def __init__(self):
#         super().__init__()
#         self.has_rd = False
#         self.mnemonic = 'cmp'

# @InstrClass
# class NegShiftedReg(ArithShiftedReg):
#     def __init__(self):
#         super().__init__()
#         self.has_rd = False
#         self.mnemonic = 'neg'

# @InstrClass
# class NegsShiftedReg(ArithShiftedReg):
#     def __init__(self):
#         super().__init__()
#         self.has_rd = False
#         self.mnemonic = 'negs'

# class ArithExtendedReg(AArch64Instr):
#     def __init__(self):
#         super().__init__()
#         self.has_shift = False
#         self.has_imm = False
#         self.amount_width = 3

#     @vsc.constraint
#     def reg_ops(self):
#         self.rn != instr_pkg.Reg.ZERO
#         self.rm != instr_pkg.Reg.SP
#         self.rm != instr_pkg.Reg.ZERO
#         self.rd != instr_pkg.Reg.ZERO
#         self.amount <= 4

# @InstrClass
# class AddExtendedReg(ArithExtendedReg):
#     def __init__(self):
#         super().__init__()
#         self.mnemonic = 'add'

# @InstrClass
# class AddsExtendedReg(ArithExtendedReg):
#     def __init__(self):
#         super().__init__()
#         self.mnemonic = 'adds'

#     @vsc.constraint
#     def rd_sp(self):
#         self.rd != instr_pkg.Reg.SP

# @InstrClass
# class SubExtendedReg(ArithExtendedReg):
#     def __init__(self):
#         super().__init__()
#         self.mnemonic = 'sub'

# @InstrClass
# class SubsExtendedReg(ArithExtendedReg):
#     def __init__(self):
#         super().__init__()
#         self.mnemonic = 'subs'

#     @vsc.constraint
#     def rd_sp(self):
#         self.rd != instr_pkg.Reg.SP

# @InstrClass
# class CmnExtendedReg(ArithExtendedReg):
#     def __init__(self):
#         super().__init__()
#         self.mnemonic = 'cmn'
#         self.has_rd = False

# @InstrClass
# class CmpExtendedReg(ArithExtendedReg):
#     def __init__(self):
#         super().__init__()
#         self.mnemonic = 'cmp'
#         self.has_rd = False

# @InstrClass
# class Adc(AArch64Instr):
#     def __init__(self):
#         super().__init__()
#         self.has_shift = False
#         self.has_extend = False
#         self.has_imm = False
#         self.mnemonic = 'adc'

#     @vsc.constraint
#     def r_sp_zero(self):
#         self.rn != instr_pkg.Reg.SP
#         self.rn != instr_pkg.Reg.ZERO
#         self.rm != instr_pkg.Reg.SP
#         self.rm != instr_pkg.Reg.ZERO
#         self.rd != instr_pkg.Reg.SP
#         self.rd != instr_pkg.Reg.ZERO

# @InstrClass
# class Adcs(Adc):
#     def __init__(self):
#         super().__init__()
#         self.mnemonic = 'adcs'

# @InstrClass
# class Sbc(Adc):
#     def __init__(self):
#         super().__init__()
#         self.mnemonic = 'sbc'

# logic shifted register

# move register

# shift register

# data processing
# data processing immediate
# arithmetic
# add, adds, sub, subs, cmp, cmn


@vsc.randobj
class ArithmeticImm:
    def __init__(self) -> None:
        self.variant_64bit = vsc.rand_bit_t(1)
        self.rd = vsc.rand_enum_t(Reg)
        self.rn = vsc.rand_enum_t(Reg)
        self.imm = vsc.rand_bit_t(12)
        self.is_add = vsc.rand_bit_t(1)
        self.signed = vsc.rand_bit_t(1)
        self.shift = vsc.rand_bit_t(1)

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

        ret += f' {instr_pkg.reg_name(self.rd, self.variant_64bit)}'
        ret += f' ,{instr_pkg.reg_name(self.rn, self.variant_64bit)}'
        ret += f', #{self.imm:#x}'
        if self.shift:
            ret += ',LSL #12'

        return ret


@vsc.randobj
class ArithmeticShiftedRegister:
    def __init__(self) -> None:
        self.variant_64bit = vsc.rand_bit_t(1)
        self.rd = vsc.rand_enum_t(Reg)
        self.rn = vsc.rand_enum_t(Reg)
        self.rm = vsc.rand_enum_t(Reg)
        self.mnemonic = vsc.rand_enum_t(Mnemonic)
        self.shift_type = vsc.rand_enum_t(instr_pkg.ShiftType)
        self.amount = vsc.rand_bit_t(6)

    @vsc.constraint
    def arithmetic_shifted_registers_cons(self):
        # self.rm != Reg.ZERO
        # self.rm != Reg.SP
        # self.rd != Reg.SP
        # self.rd != Reg.ZERO
        # self.rn != Reg.SP
        # self.rn != Reg.ZERO
        self.mnemonic in vsc.rangelist(Mnemonic.ADD, Mnemonic.ADDS, Mnemonic.SUB,
                                       Mnemonic.SUBS, Mnemonic.CMN, Mnemonic.CMP, Mnemonic.NEG, Mnemonic.NEGS)
        self.shift_type in vsc.rangelist(
            ShiftType.LSL, ShiftType.LSR, ShiftType.ASR)

    def convert2asm(self):
        ret = f'{self.mnemonic.name}'
        first_reg = True
        if self.mnemonic == Mnemonic.CMN or self.mnemonic == Mnemonic.CMP:
            pass
        else:
            ret += f' {instr_pkg.reg_name(self.rd, self.variant_64bit)}'
            first_reg = False

        if self.mnemonic == Mnemonic.NEG or self.mnemonic == Mnemonic.NEGS:
            pass
        else:
            if first_reg:
                first_reg = False
            else:
                ret += ', '
            ret += f' {instr_pkg.reg_name(self.rn, self.variant_64bit)}'

        ret += f', {instr_pkg.reg_name(self.rm, self.variant_64bit)}'
        ret += f', {self.shift_type.name}'
        amount = self.amount
        if not self.variant_64bit:
            amount = amount & 0x1F
        ret += f' #{amount:#x}'
        return ret

# loads and stores
# load/store immediate


@vsc.randobj
class LdStImm:
    # LDR(LDRW) LDRB(w), LDRH(w), LDRSB, LDRSH, LDRSW

    def __init__(self) -> None:
        # support post_index with unscaled offset only
        self.post_index = True
        self.pre_index = False
        self.unsigned_offset = True

        # self.variant_64bit = vsc.rand_bit_t(1)
        self.rt = vsc.rand_enum_t(instr_pkg.Reg)
        self.rn = vsc.rand_enum_t(instr_pkg.Reg)
        # self.simm = vsc.rand_int_t(9)
        self.pimm = vsc.rand_bit_t(12)
        self.data_size = vsc.rand_bit_t(4)
        self.is_load = vsc.rand_bit_t(1)
        self.is_signed = vsc.rand_bit_t(1)
        self.target_64bit = vsc.rand_bit_t(1)

    @vsc.constraint
    def ld_st_imm_cons(self):
        # self.rt != instr_pkg.Reg.SP
        # self.rt != instr_pkg.Reg.ZERO
        # self.rn != instr_pkg.Reg.ZERO
        self.rt != self.rn
        self.data_size in vsc.rangelist(1, 2, 4, 8)
        with vsc.if_then(self.is_load):
            with vsc.if_then(self.is_signed):
                self.data_size != 8
                # signed extension
                with vsc.if_then(self.data_size == 4):
                    # word can only be extended to 64bit
                    self.target_64bit == 1
            with vsc.else_then():
                # no signed extension
                with vsc.if_then(self.data_size == 8):
                    self.target_64bit == 1
                with vsc.else_then():
                    self.target_64bit == 0
        with vsc.else_then():
            with vsc.if_then(self.data_size == 8):
                self.target_64bit == 1
            with vsc.else_then():
                self.target_64bit == 0

    def convert2asm(self) -> str:
        ret = ''
        if bool(self.is_load):
            ret = 'ldr'
        else:
            ret = 'str'

        if bool(self.is_load) and bool(self.is_signed):
            ret += 's'

        match self.data_size:
            case 8:
                pass
            case 4:
                if bool(self.is_load) and bool(self.is_signed):
                    ret += 'w'
            case 2:
                ret += 'h'
            case 1:
                ret += 'b'

        ret += f' {instr_pkg.reg_name(self.rt, self.target_64bit)}'
        ret += f', [{instr_pkg.reg_name(self.rn, True)}'
        ret += f', #{self.pimm*self.data_size}]'

        return ret

# load/store register

# logger.info('after ldrimm')

# class LdrReg(LdrImm):
#     def __init__(self):
#         super().__init__()

# logger.info('after ldrreg')


class VerbatimInstScope:
    def __init__(self):
        self.inst_seq = []

    def __enter__(self):
        global verbatim_inst_scope
        assert (verbatim_inst_scope is None)
        verbatim_inst_scope = self
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        global verbatim_inst_scope
        verbatim_inst_scope = None


verbatim_inst_scope: VerbatimInstScope = None


class VerbatimInst:
    def __init__(self, inst_str: str = None) -> None:
        self.inst_str = inst_str
        if verbatim_inst_scope is not None:
            verbatim_inst_scope.inst_seq.append(self)

    def convert2asm(self):
        return self.inst_str
