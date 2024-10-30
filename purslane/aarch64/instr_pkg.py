"""
author: zuoqian
Copyright 2024. All rights reserved.
"""

from enum import Enum, IntEnum, auto

class Imm(IntEnum):
    IMM = 0 # signed immediate
    UIMM = auto() # unsigned immediate
    NZUIMM = auto() # non-zero unsigned immediate
    NZIMM = auto() # non-zero signed immediate

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


# class InstrName(IntEnum):
#     # load/store register
#     LDR = 0
#     LDRB = auto()
#     LDRSB = auto()
#     LDRH = auto()
#     LDRSH = auto()
#     LDRSW = auto()
#     STR = auto()
#     STRB = auto()
#     STRH = auto()
#     # load/store register(unscaled offset)
#     LDUR = auto()
#     LDURB = auto()
#     LDURSB = auto()
#     LDURH = auto()
#     LDURSH = auto()
#     LDURSW = auto()
#     STUR = auto()
#     STURB = auto()
#     STURH = auto()
#     # load/store pair
#     LDP = auto()
#     LDPSW = auto()
#     STP = auto()
#     # load/store non-temporal pair
#     LDNP = auto()
#     STNP = auto()
#     # load/store unprivileged
#     LDTR = auto()
#     LDTRB = auto()
#     LDTRSB = auto()
#     LDTRH = auto()
#     LDTRSH = auto()
#     LDTRSW = auto()
#     STTR = auto()
#     STTRB = auto()
#     STTRH = auto()
#     # load-exclusive/store-exclusive
#     LDXR = auto()
#     LDXRB = auto()
#     LDXRH = auto()
#     LDXP = auto()
#     STXR = auto()
#     STXRB = auto()
#     STXRH = auto()
#     STXP = auto()
#     # load-acquire/store-release
#     LDAR = auto()
#     LDARB = auto()
#     LDARH = auto()
#     STLR = auto()
#     STLRB = auto()
#     STLRH = auto()
#     # exclusive load-acquire and store-release instructions
#     LDAXR = auto()
#     LDAXRB = auto()
#     LDAXRH = auto()
#     LDAXP = auto()
#     STLXR = auto()
#     STLXRB = auto()
#     STLXRH = auto()
#     STLXP = auto()

#     # data processing - immediate
#     # arithmetic
#     ADD = auto() # add rd|sp, rn|sp, #<imm12> {, <shift2, LSL #0, LSL #12>}
#     ADDS = auto() # adds rd, rn|sp, #<imm12> {, <shift2>}
#     SUB = auto() # sub rd|sp, rn|sp, #<imm12> {, <shift2>}
#     SUBS = auto() # subs rd, rn|sp, #<imm12> {, <shift2>}
#     CMP = auto() # cmp rn|sp, #<imm12>, {, <shift2>} || subs wxzr, rn|sp, #<imm12>, {, <shift2>}
#     CMN = auto() # cmp rn|sp, #<imm12>, {, <shift2>} || adds wxzr, rn|sp, #<imm12>, {, <shift2>}
#     # logical
#     AND = auto() # and rd|sp, rn, #<imm12>
#     ANDS = auto() # ands rd, rn, #<imm12>
#     EOR = auto() # eor rd|sp, rn, #<imm12>
#     ORR = auto() # orr rd|sp, rn, #<imm12>
#     TST = auto() # tst rn, #<imm12> || ands wzr, rn, #<imm12>
#     # move wide immediate
#     MOVZ = auto() # movz rd, #<imm16> {, LSL #<shift2>}
#     MOVN = auto() # movn rd, #<imm16> {, LSL #<shift2>}
#     MOVK = auto() # movk rd, #<imm16> {, LSL #<shift2>}
#     # move immediate
#     MOV = auto() # 
#     # pc-relative address calculation
#     ADRP = auto()
#     ADR = auto()
#     # bitfield move
#     BFM = auto() # bfm rd, rn, #<immr6>, #<imms6>
#     SBFM = auto() # sbfm rd, rn, #<immr6>, #<imms6>
#     UBFM = auto() # ubfm rd, rn, #<immr6>, #<imms6>
#     # bitfield insert and extract
#     BFI = auto() # -> BFM
#     BFXIL = auto() # -> BFM
#     SBFIZ = auto() # -> SBFM
#     SBFX = auto() # -> SBFM
#     UBFIZ = auto() # -> UBFM
#     UBFX = auto() # -> UBFM
#     # extract register
#     EXTR = auto() # extr rd, rn, rm, #<lsb5|6>
#     # shift
#     ASR = auto() # -> SBFM
#     LSL = auto() # -> UBFM
#     LSR = auto() # -> UBFM
#     ROR = auto() # -> EXTR
#     # sign-extend and zero-extend
#     SXTB = auto() # -> SBFM
#     SXTH = auto() # -> SBFM
#     SXTW = auto() # -> SBFM
#     UXTB = auto() # -> UBFM
#     UXTH = auto() # -> UBFM

#     # data processing - register
#     ADD_shifted_register = auto() # add rd, rn, rm{, <shift2> #<amount>}
#     # arithmetic with carry
#     ADC = auto() # adc rd, rn, rm
#     ADCS = auto()
#     SBC = auto()
#     SBCS = auto()
#     NGC = auto()
#     NGCS = auto()
#     # logical shifted register
#     BIC = auto()
#     BICS = auto()
#     EON = auto()
