"""
author: zuoqian
Copyright 2024. All rights reserved.
"""

import logging
import random
import sys
import vsc

from purslane.aarch64 import instr_pkg

logger = logging.getLogger('aarch64.isa.instr')

@vsc.randobj
class Instr:
    instr_registry = []

    def __init__(self) -> None:
        # attributes
        # self.group = vsc.enum_t(instr_pkg.)
        self.instr_name = None
        self.mnemonic = None
        self.variant_64bit = vsc.rand_bit_t(1)

        # operands
        self.rm = vsc.rand_enum_t(instr_pkg.Reg)
        self.rn = vsc.rand_enum_t(instr_pkg.Reg)
        self.rd = vsc.rand_enum_t(instr_pkg.Reg)
        self.imm = vsc.rand_bit_t(16)
        self.imm_N = vsc.rand_bit_t(1)
        self.immr = vsc.rand_bit_t(6)
        self.imms = vsc.rand_bit_t(6)
        self.shift_type = vsc.rand_enum_t(instr_pkg.ShiftType)
        self.extend_type = vsc.rand_enum_t(instr_pkg.ExtendType)
        self.amount = vsc.rand_bit_t(16)

        # helper fields
        self.has_rm = True
        self.has_rn = True
        self.has_rd = True
        self.has_imm = True
        self.has_shift = True
        self.has_extend = True

        self.imm_width = 16
        self.amount_width = 16
        self.use_bitmask_imm = False

    # @classmethod
    # def CreateInstrList(self, cfg = None):
    #     pass

    # @classmethod
    # def CreateInstr(self, instr_name, instr_group):
    #     pass

    @classmethod
    def register(cls, instr_cls):
        logger.info(f'instr register {instr_cls}')
        cls.instr_registry.append(instr_cls)

    @classmethod
    def get_rand_instr(cls):
        return random.choice(cls.instr_registry)()
    
    # @vsc.constraint
    # def zero_imm_N_32bit(self):
    #     with vsc.if_then(not self.variant_64bit):
    #         self.imm_N == 0

    def pre_randomize(self):
        logger.info('instr pre-randomize')
        self.rn.rand_mode = self.has_rn
        self.rm.rand_mode = self.has_rm
        self.rd.rand_mode = self.has_rd
        self.extend_type.rand_mode = self.has_extend

        # if self.has_rn:
        #     if not self.zero_allowed_rn:
        #         self.rn_zero.constraint_mode = False
        #     if not self.sp_allowed_rn:
        #         self.rn_sp.constraint_mode = False

        # if self.has_rm:
        #     if not self.zero_allowed_rm:
        #         self.rm_zero.constraint_mode = False
        #     if not self.sp_allowed_rm:
        #         self.rm_sp.constraint_mode = False

        # if self.has_rd:
        #     if not self.zero_allowed_rd:
        #         self.rd_zero.constraint_mode = False
        #     if not self.sp_allowd_rd:
        #         self.rd_sp.constraint_mode = False

    def post_randomize(self):
        pass

    def decode_bit_masks(self) -> int:
        # decode bit masks
        imms_7 = vsc.bit_t(7)
        imms_7[5:0] = ~self.imms
        if bool(self.variant_64bit):
            imms_7[0] = self.imm_N
            wmask = vsc.bit_t(64)
            tmask = vsc.bit_t(64)
        else:
            imms_7[0] = 0
            wmask = vsc.bit_t(32)
            tmask = vsc.bit_t(64)

        for length in range(6, 0, -1):
            if imms_7[length] != 0:
                break
        print(f'len {length}')
        
        levels = vsc.bit_t(6)
        for i in range(length):
            levels[i] = 1
        print(f'lelves {levels.val:#x}')
        

        s = self.imms & levels
        r = self.immr & levels
        diff = s - r

        esize = 1 << length
        d = diff

        return 0
        

    def convert2asm(self) -> str:
        v64 = bool(self.variant_64bit)
        ret = self.mnemonic + ' '
        first_reg = True
        if self.has_rd:
            ret += instr_pkg.reg_name(self.rd, v64)
            first_reg = False
        if self.has_rn:
            if not first_reg:
                ret += ', '
            ret += instr_pkg.reg_name(self.rn, v64)
            first_reg = False
        if self.has_rm:
            assert(not first_reg)
            ret += f', {instr_pkg.reg_name(self.rm, v64)}'
        if self.has_imm:
            if self.use_bitmask_imm:
                ret += f', #{self.decode_bit_masks():#x}'
            else:
                ret += f', #{self.imm[self.imm_width-1:0]:#x}'
        if self.has_shift:
            ret += f', {self.shift_type.name} #{self.amount[self.amount_width-1:0]}'
        if self.has_extend:
            ret += f', {self.extend_type.name} #{self.amount[self.amount_width-1:0]}'
        return ret
        