import logging
import argparse
import random
from enum import Enum
from mint import moesi
from mint.moesi import Cacheline
import purslane
from purslane.dsl import Do, Action, Sequence, Parallel, Select, Run, TypeOverride
from purslane.dsl import RandU8, RandU16, RandU32, RandU64, RandUInt, RandS8, RandS16, RandS32, RandS64, RandInt
from purslane.addr_space import AddrSpace
from purslane.addr_space import SMWrite8, SMWrite16, SMWrite32, SMWrite64, SMWriteBytes
from purslane.addr_space import SMRead8, SMRead16, SMRead32, SMRead64, SMReadBytes

# 获取目标平台配置
import ivy_app_cfg

logger = logging.getLogger('aarch64_moesi')

# cacheline 尺寸
CACHELINE_SIZE = 64
# 每个 cacheline 内分配的存储尺寸，由于指令访问一般无法访问整个 cacheline，为了提高碰撞
# 一般不会使用整个cacheine
MEMCELL_SIZE = 16

ASSOCIATIVITY = 4
NUM_SETS = 1024




class Size(Enum):
    Byte = 0
    HalfWord = 1
    Word = 2
    DoubleWord = 3

    def ByteSize(self) -> int:
        return 1 << self.value

    def BitWidth(self) -> int:
        return 8*self.ByteSize()

    def RegName(self) -> str:
        if self.value == 3:
            return 'x'
        return 'w'

    def InstSuffix(self) -> str:
        if self.value == 1:
            return 'h'
        if self.value == 0:
            return 'b'
        return ''

# dw = Size.DoubleWord
# print(dw.RegName())


def CheckValue(var: str, addr: int, value: int):
    # return ''
    return f"""
        if({var} != {value:#x}){{
            printf("check value failed, addr: {addr:#x}, value expected: {value: #x}, value read: %x\\n", {var});
            xrt_exit(1);
        }}
        """


class LSType(Enum):
    Ordinary = 0
    Unpriviledged = 1
    AcquireRelease = 3
    LO = 2


def LoadInst(s: Size, t: LSType) -> str:
    match t:
        case LSType.Ordinary:
            inst = 'ldr'
        case LSType.Unpriviledged:
            inst = 'ldtr'
        case LSType.AcquireRelease:
            inst = 'ldar'
        case LSType.LO:
            inst = 'ldlar'

    if s == Size.HalfWord:
        return inst+'h'
    if s == Size.Byte:
        return inst+'b'
    return inst


def StoreInst(s: Size, t: LSType) -> str:
    match t:
        case LSType.Ordinary:
            inst = 'str'
        case LSType.Unpriviledged:
            inst = 'sttr'
        case LSType.AcquireRelease:
            inst = 'stlr'
        case LSType.LO:
            inst = 'stllr'

    if s == Size.HalfWord:
        return inst+'h'
    if s == Size.Byte:
        return inst+'b'
    return inst

# Load/Store Register, unpriviledged, LO


class LDR_GEN(Action):
    def __init__(self, addr: int, size: Size, lstype: LSType, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr
        self.size = size
        self.lstype = lstype

    def Body(self):
        byte_size = self.size.ByteSize()
        byte_val = SMReadBytes(self.addr, byte_size)
        int_val = int.from_bytes(byte_val, 'little')
        inst = LoadInst(self.size, self.lstype)
        self.c_src = f'uint{self.size.BitWidth()}_t v; asm volatile("{inst} %{self.size.RegName()}0, [%1]" : "=&r"(v) : "r" ({self.addr:#x}));'
        self.c_src += CheckValue('v', self.addr, int_val)


class STR_GEN(Action):
    def __init__(self, addr: int, size: Size, lstype: LSType, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr
        self.size = size
        self.lstype = lstype

    def Body(self):
        byte_size = self.size.ByteSize()
        bit_width = self.size.BitWidth()
        value = RandUInt(bit_width)
        byte_value = value.to_bytes(byte_size, 'little')
        SMWriteBytes(self.addr, byte_value)
        inst = StoreInst(self.size, self.lstype)
        self.c_src = f'asm volatile("{inst} %{self.size.RegName()}1, [%0]" : : "r" ({self.addr:#x}), "r" ({value:#x}));'

# load/store


class LDR(LDR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, LSType.Ordinary, name)


class LDRW(LDR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, LSType.Ordinary, name)


class LDRH(LDR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, LSType.Ordinary, name)


class LDRB(LDR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, LSType.Ordinary, name)


class STR(STR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, LSType.Ordinary, name)


class STRW(STR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, LSType.Ordinary, name)


class STRH(STR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, LSType.Ordinary, name)


class STRB(STR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, LSType.Ordinary, name)


# load/store unpriviledged
class LDTR(LDR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, LSType.Unpriviledged, name)


class LDTRW(LDR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, LSType.Unpriviledged, name)


class LDTRH(LDR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, LSType.Unpriviledged, name)


class LDTRB(LDR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, LSType.Unpriviledged, name)


class STTR(STR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, LSType.Unpriviledged, name)


class STTRW(STR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, LSType.Unpriviledged, name)


class STTRH(STR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, LSType.Unpriviledged, name)


class STTRB(STR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, LSType.Unpriviledged, name)

# load-acquire/store-release


class LDAR(LDR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, LSType.AcquireRelease, name)


class LDARW(LDR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, LSType.AcquireRelease, name)


class LDARH(LDR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, LSType.AcquireRelease, name)


class LDARB(LDR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, LSType.AcquireRelease, name)


class STLR(STR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, LSType.AcquireRelease, name)


class STLRW(STR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, LSType.AcquireRelease, name)


class STLRH(STR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, LSType.AcquireRelease, name)


class STLRB(STR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, LSType.AcquireRelease, name)


# load/store LO
class LDLAR(LDR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, LSType.LO, name)


class LDLARW(LDR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, LSType.LO, name)


class LDLARH(LDR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, LSType.LO, name)


class LDLARB(LDR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, LSType.LO, name)


class STLLR(STR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, LSType.LO, name)


class STLLRW(STR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, LSType.LO, name)


class STLLRH(STR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, LSType.LO, name)


class STLLRB(STR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, LSType.LO, name)


# Load/Store Pair


class LDP_GEN(Action):
    def __init__(self, addr: int, non_tmp: bool, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr
        self.non_tmp = non_tmp

    def Body(self):
        v0 = SMRead64(self.addr)
        v1 = SMRead64(self.addr+8)
        inst = 'ldnp' if self.non_tmp else 'ldp'
        self.c_src = f'uint64_t v0; uint64_t v1; asm volatile("{inst} %x0, %x1, [%2]" : "=&r"(v0), "=&r"(v1) : "r" ({self.addr:#x}));\n'
        self.c_src += CheckValue('v0', self.addr, v0)
        self.c_src += CheckValue('v1', self.addr+8, v1)


class STP_GEN(Action):
    def __init__(self, addr: int, non_tmp: bool, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr
        self.non_tmp = non_tmp

    def Body(self):
        v0 = RandU64()
        v1 = RandU64()
        SMWrite64(self.addr, v0)
        SMWrite64(self.addr+8, v1)
        inst = 'stnp' if self.non_tmp else 'stnp'
        self.c_src = f'asm volatile("{inst} %x1, %x2, [%0]" : : "r" ({self.addr:#x}), "r" ({v0:#x}), "r" ({v1:#x}));'


class LDPW_GEN(Action):
    def __init__(self, addr: int, non_tmp: bool, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr
        self.non_tmp = non_tmp

    def Body(self):
        v0 = SMRead32(self.addr)
        v1 = SMRead32(self.addr+4)
        inst = 'ldnp' if self.non_tmp else 'ldp'
        self.c_src = f'uint32_t v0; uint32_t v1; asm volatile("{inst} %w0, %w1, [%2]" : "=&r"(v0), "=&r"(v1) : "r" ({self.addr:#x}));\n'
        self.c_src += CheckValue('v0', self.addr, v0)
        self.c_src += CheckValue('v1', self.addr+4, v1)


class STPW_GEN(Action):
    def __init__(self, addr: int, non_tmp: bool, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr
        self.non_tmp = non_tmp

    def Body(self):
        v0 = RandU32()
        v1 = RandU32()
        SMWrite32(self.addr, v0)
        SMWrite32(self.addr+8, v1)
        inst = 'stnp' if self.non_tmp else 'stnp'
        self.c_src = f'asm volatile("{inst} %w1, %w2, [%0]" : : "r" ({self.addr:#x}), "r" ({v0:#x}), "r" ({v1:#x}));'

# ldp/stp


class LDP(LDP_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, False, name)


class LDPW(LDPW_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, False, name)


class STP(STP_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, False, name)


class STPW(STPW_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, False, name)

# ldp/stp non-temporaral


class LDNP(LDP_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, False, name)


class LDNPW(LDPW_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, False, name)


class STNP(STP_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, False, name)


class STNPW(STPW_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, False, name)


# Load-Exclusive/Store-Exclusive


class LDXR_GEN(Action):
    def __init__(self, addr: int, size: Size, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr
        self.size = size

    def Body(self):
        byte_size = self.size.ByteSize()
        byte_val = SMReadBytes(self.addr, byte_size)
        int_val = int.from_bytes(byte_val, 'little')
        self.c_src = f'uint{self.size.BitWidth()}_t v; asm volatile("ldxr{self.size.InstSuffix()} %{self.size.RegName()}0, [%1]" : "=&r"(v) : "r" ({self.addr:#x}));'
        self.c_src += CheckValue('v', self.addr, int_val)


class STXR_GEN(Action):
    def __init__(self, addr: int, size: Size, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr
        self.size = size

    def Body(self):
        byte_size = self.size.ByteSize()
        bit_width = self.size.BitWidth()

        old_byte_value = SMReadBytes(self.addr, byte_size)
        old_int_value = int.from_bytes(old_byte_value, 'little')

        new_int_value = RandUInt(bit_width)
        new_byte_value = new_int_value.to_bytes(byte_size, 'little')
        SMWriteBytes(self.addr, new_byte_value)

        inst_suffix = self.size.InstSuffix()
        reg_name = self.size.RegName()

        self.c_src = f"""
        uint32_t res;
        uint{bit_width}_t ov = {old_int_value:#x};
        uint{bit_width}_t nv = {new_int_value:#x};
        do{{
            asm volatile(
                "ldxr{inst_suffix} %{reg_name}1, [%2];"
                "mov %{reg_name}1, %{reg_name}3;"
                "stxr{inst_suffix} %w0, %{reg_name}1, [%2]"
                : "=&r"(res), "=&r"(ov)
                : "r" ({self.addr:#x}), "r"(nv)
                );
        }}while(res);
        """
        CheckValue('old_val', self.addr, old_int_value)

# load-exclusive/store-exclusive


class LDXR(LDXR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, name)


class LDXRW(LDXR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, name)


class LDXRH(LDXR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, name)


class LDXRB(LDXR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, name)


class STXR(STXR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, name)


class STXRW(STXR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, name)


class STXRH(STXR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, name)


class STXRB(STXR_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, name)


class LDXP(Action):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Body(self):
        v0 = SMRead64(self.addr)
        v1 = SMRead64(self.addr+8)
        self.c_src = f'uint64_t v0; uint64_t v1; asm volatile("ldxp %x0, %x1, [%2]" : "=&r"(v0), "=&r"(v1) : "r" ({self.addr:#x}));\n'
        self.c_src += CheckValue('v0', self.addr, v0)
        self.c_src += CheckValue('v1', self.addr+8, v1)


class STXP(Action):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Body(self):
        old_v0 = SMRead64(self.addr)
        old_v1 = SMRead64(self.addr)
        new_v0 = RandU64()
        new_v1 = RandU64()
        SMWrite64(self.addr, new_v0)
        SMWrite64(self.addr+8, new_v1)
        self.c_src = f"""
        uint32_t res;
        uint64_t ov0 = {old_v0:#x};
        uint64_t ov1 = {old_v1:#x};
        uint64_t nv0 = {new_v0:#x};
        uint64_t nv1 = {new_v1:#x};
        do{{
            asm volatile(
                "ldxp %x1, %x2, [%3];"
                "mov %x1, %x4;"
                "mov %x2, %x5;"
                "stxp %w0, %x1, %x2, [%3]"
                : "=&r"(res), "=&r"(ov0), "=&r"(ov1)
                : "r" ({self.addr:#x}), "r"(nv0), "r"(nv1)
                );
        }}while(res);
        """
        CheckValue('ov0', self.addr, old_v0)
        CheckValue('ov1', self.addr+8, old_v1)

# Atomic Instructions


class AtomicOp(Enum):
    Add = 0
    Clr = 1
    Eor = 2
    Set = 3
    Max = 4
    Min = 5
    UMax = 6
    UMin = 7

AtomicOpInstTab = {
    AtomicOp.Add: 'add',
    AtomicOp.Clr: 'clr',
    AtomicOp.Eor: 'eor',
    AtomicOp.Set: 'set',
    AtomicOp.Max: 'smax',
    AtomicOp.Min: 'smin',
    AtomicOp.UMax: 'umax',
    AtomicOp.UMin: 'umin'
}


class AtomicLDST_GEN(Action):
    def __init__(self, addr: int, size: Size, op: AtomicOp, ld: bool, acquire: bool, release: bool, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr
        self.size = size
        self.op = op
        self.ld = ld
        self.acquire = acquire
        self.release = release

    def Body(self):
        byte_size = self.size.ByteSize()
        bit_width = byte_size*8
        byte_mask = bytearray(byte_size)
        for i in range(byte_size):
            byte_mask[i] = 0xFF
        mask = int.from_bytes(byte_mask, 'little')

        old_byte_val = SMReadBytes(self.addr, byte_size)

        old_uint_val = int.from_bytes(old_byte_val, 'little')
        old_sint_val = int.from_bytes(old_byte_val, 'little', signed=True)

        match self.op:
            case AtomicOp.Add:
                op_int_val = RandUInt(bit_width)
                new_int_val = (old_uint_val+op_int_val) & mask
                new_byte_val = new_int_val.to_bytes(byte_size, 'little')
            case AtomicOp.Clr:
                op_int_val = RandUInt(bit_width)
                new_int_val = old_uint_val & (~op_int_val)
                new_byte_val = new_int_val.to_bytes(byte_size, 'little')
            case AtomicOp.Eor:
                op_int_val = RandUInt(bit_width)
                new_int_val = old_uint_val ^ op_int_val
                new_byte_val = new_int_val.to_bytes(byte_size, 'little')
            case AtomicOp.Set:
                op_int_val = RandUInt(bit_width)
                new_int_val = old_uint_val | op_int_val
                new_byte_val = new_int_val.to_bytes(byte_size, 'little')
            case AtomicOp.Max:
                op_int_val = RandInt(bit_width)
                new_int_val = max(old_sint_val, op_int_val)
                new_byte_val = new_int_val.to_bytes(
                    byte_size, 'little', signed=True)
            case AtomicOp.Min:
                op_int_val = RandInt(bit_width)
                new_int_val = min(old_sint_val, op_int_val)
                new_byte_val = new_int_val.to_bytes(
                    byte_size, 'little', signed=True)
            case AtomicOp.UMax:
                op_int_val = RandUInt(bit_width)
                new_int_val = max(old_uint_val, op_int_val)
                new_byte_val = new_int_val.to_bytes(
                    byte_size, 'little', signed=False)
            case AtomicOp.UMin:
                op_int_val = RandUInt(bit_width)
                new_int_val = min(old_uint_val, op_int_val)
                new_byte_val = new_int_val.to_bytes(
                    byte_size, 'little', signed=False)

        SMWriteBytes(self.addr, new_byte_val)
        inst_ldst = 'ld' if self.ld else 'st'
        inst_op = AtomicOpInstTab[self.op]
        inst_a = 'a' if self.acquire else ''
        inst_l = 'l' if self.release else ''
        inst_bw = ''
        if self.size == Size.HalfWord:
            inst_bw = 'h'
        elif self.size == Size.Byte:
            inst_bw = 'b'

        inst = f'{inst_ldst}{inst_op}{inst_a}{inst_l}{inst_bw}'
        reg_name = 'x' if self.size == Size.DoubleWord else 'w'

        if self.ld:
            self.c_src = f"""
            uint{bit_width}_t ov;
            asm volatile("{inst} %{reg_name}1, %{reg_name}0, [%2]" : "=&r"(ov) : "r" ({op_int_val:#x}), "r" ({self.addr:#x}));
            """
        else:
            self.c_src = f"""
            uint{bit_width}_t ov;
            asm volatile("{inst} %{reg_name}0, [%1]" : : "r" ({op_int_val:#x}), "r" ({self.addr:#x}));
            """

        if self.ld:
            # use unsigned old value to check
            self.c_src += CheckValue('ov', self.addr, old_uint_val)

# atomic load


class LDADD(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Add,
                         ld=True, acquire=False, release=False, name=name)


class LDADDW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Add,
                         ld=True, acquire=False, release=False, name=name)


class LDADDH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Add,
                         ld=True, acquire=False, release=False, name=name)


class LDADDB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Add,
                         ld=True, acquire=False, release=False, name=name)


class LDCLR(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Clr,
                         ld=True, acquire=False, release=False, name=name)


class LDCLRW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Clr,
                         ld=True, acquire=False, release=False, name=name)


class LDCLRH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Clr,
                         ld=True, acquire=False, release=False, name=name)


class LDCLRB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Clr,
                         ld=True, acquire=False, release=False, name=name)


class LDEOR(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Eor,
                         ld=True, acquire=False, release=False, name=name)


class LDEORW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Eor,
                         ld=True, acquire=False, release=False, name=name)


class LDEORH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Eor,
                         ld=True, acquire=False, release=False, name=name)


class LDEORB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Eor,
                         ld=True, acquire=False, release=False, name=name)


class LDSET(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Set,
                         ld=True, acquire=False, release=False, name=name)


class LDSETW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Set,
                         ld=True, acquire=False, release=False, name=name)


class LDSETH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Set,
                         ld=True, acquire=False, release=False, name=name)


class LDSETB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Set,
                         ld=True, acquire=False, release=False, name=name)


class LDMAX(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Max,
                         ld=True, acquire=False, release=False, name=name)


class LDMAXW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Max,
                         ld=True, acquire=False, release=False, name=name)


class LDMAXH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Max,
                         ld=True, acquire=False, release=False, name=name)


class LDMAXB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Max,
                         ld=True, acquire=False, release=False, name=name)


class LDMIN(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Min,
                         ld=True, acquire=False, release=False, name=name)


class LDMINW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Min,
                         ld=True, acquire=False, release=False, name=name)


class LDMINH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Min,
                         ld=True, acquire=False, release=False, name=name)


class LDMINB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Min,
                         ld=True, acquire=False, release=False, name=name)


class LDUMAX(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.UMax,
                         ld=True, acquire=False, release=False, name=name)


class LDUMAXW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.UMax,
                         ld=True, acquire=False, release=False, name=name)


class LDUMAXH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.UMax,
                         ld=True, acquire=False, release=False, name=name)


class LDUMAXB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.UMax,
                         ld=True, acquire=False, release=False, name=name)


class LDUMIN(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.UMin,
                         ld=True, acquire=False, release=False, name=name)


class LDUMINW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.UMin,
                         ld=True, acquire=False, release=False, name=name)


class LDUMINH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.UMin,
                         ld=True, acquire=False, release=False, name=name)


class LDUMINB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.UMin,
                         ld=True, acquire=False, release=False, name=name)


# atomic load acquire
class LDADDA(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Add,
                         ld=True, acquire=True, release=False, name=name)


class LDADDAW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Add,
                         ld=True, acquire=True, release=False, name=name)


class LDADDAH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Add,
                         ld=True, acquire=True, release=False, name=name)


class LDADDAB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Add,
                         ld=True, acquire=True, release=False, name=name)


class LDCLRA(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Clr,
                         ld=True, acquire=True, release=False, name=name)


class LDCLRAW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Clr,
                         ld=True, acquire=True, release=False, name=name)


class LDCLRAH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Clr,
                         ld=True, acquire=True, release=False, name=name)


class LDCLRAB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Clr,
                         ld=True, acquire=True, release=False, name=name)


class LDEORA(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Eor,
                         ld=True, acquire=True, release=False, name=name)


class LDEORAW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Eor,
                         ld=True, acquire=True, release=False, name=name)


class LDEORAH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Eor,
                         ld=True, acquire=True, release=False, name=name)


class LDEORAB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Eor,
                         ld=True, acquire=True, release=False, name=name)


class LDSETA(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Set,
                         ld=True, acquire=True, release=False, name=name)


class LDSETAW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Set,
                         ld=True, acquire=True, release=False, name=name)


class LDSETAH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Set,
                         ld=True, acquire=True, release=False, name=name)


class LDSETAB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Set,
                         ld=True, acquire=True, release=False, name=name)


class LDMAXA(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Max,
                         ld=True, acquire=True, release=False, name=name)


class LDMAXAW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Max,
                         ld=True, acquire=True, release=False, name=name)


class LDMAXAH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Max,
                         ld=True, acquire=True, release=False, name=name)


class LDMAXAB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Max,
                         ld=True, acquire=True, release=False, name=name)


class LDMINA(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Min,
                         ld=True, acquire=True, release=False, name=name)


class LDMINAW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Min,
                         ld=True, acquire=True, release=False, name=name)


class LDMINAH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Min,
                         ld=True, acquire=True, release=False, name=name)


class LDMINAB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Min,
                         ld=True, acquire=True, release=False, name=name)


class LDUMAXA(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.UMax,
                         ld=True, acquire=True, release=False, name=name)


class LDUMAXAW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.UMax,
                         ld=True, acquire=True, release=False, name=name)


class LDUMAXAH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.UMax,
                         ld=True, acquire=True, release=False, name=name)


class LDUMAXAB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.UMax,
                         ld=True, acquire=True, release=False, name=name)


class LDUMINA(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.UMin,
                         ld=True, acquire=True, release=False, name=name)


class LDUMINAW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.UMin,
                         ld=True, acquire=True, release=False, name=name)


class LDUMINAH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.UMin,
                         ld=True, acquire=True, release=False, name=name)


class LDUMINAB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.UMin,
                         ld=True, acquire=True, release=False, name=name)

# atomic load acquire-release


class LDADDAL(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Add,
                         ld=True, acquire=True, release=True, name=name)


class LDADDALW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Add,
                         ld=True, acquire=True, release=True, name=name)


class LDADDALH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Add,
                         ld=True, acquire=True, release=True, name=name)


class LDADDALB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Add,
                         ld=True, acquire=True, release=True, name=name)


class LDCLRAL(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Clr,
                         ld=True, acquire=True, release=True, name=name)


class LDCLRALW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Clr,
                         ld=True, acquire=True, release=True, name=name)


class LDCLRALH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Clr,
                         ld=True, acquire=True, release=True, name=name)


class LDCLRALB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Clr,
                         ld=True, acquire=True, release=True, name=name)


class LDEORAL(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Eor,
                         ld=True, acquire=True, release=True, name=name)


class LDEORALW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Eor,
                         ld=True, acquire=True, release=True, name=name)


class LDEORALH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Eor,
                         ld=True, acquire=True, release=True, name=name)


class LDEORALB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Eor,
                         ld=True, acquire=True, release=True, name=name)


class LDSETAL(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Set,
                         ld=True, acquire=True, release=True, name=name)


class LDSETALW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Set,
                         ld=True, acquire=True, release=True, name=name)


class LDSETALH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Set,
                         ld=True, acquire=True, release=True, name=name)


class LDSETALB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Set,
                         ld=True, acquire=True, release=True, name=name)


class LDMAXAL(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Max,
                         ld=True, acquire=True, release=True, name=name)


class LDMAXALW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Max,
                         ld=True, acquire=True, release=True, name=name)


class LDMAXALH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Max,
                         ld=True, acquire=True, release=True, name=name)


class LDMAXALB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Max,
                         ld=True, acquire=True, release=True, name=name)


class LDMINAL(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Min,
                         ld=True, acquire=True, release=True, name=name)


class LDMINALW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Min,
                         ld=True, acquire=True, release=True, name=name)


class LDMINALH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Min,
                         ld=True, acquire=True, release=True, name=name)


class LDMINALB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Min,
                         ld=True, acquire=True, release=True, name=name)


class LDUMAXAL(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.UMax,
                         ld=True, acquire=True, release=True, name=name)


class LDUMAXALW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.UMax,
                         ld=True, acquire=True, release=True, name=name)


class LDUMAXALH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.UMax,
                         ld=True, acquire=True, release=True, name=name)


class LDUMAXALB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.UMax,
                         ld=True, acquire=True, release=True, name=name)


class LDUMINAL(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.UMin,
                         ld=True, acquire=True, release=True, name=name)


class LDUMINALW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.UMin,
                         ld=True, acquire=True, release=True, name=name)


class LDUMINALH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.UMin,
                         ld=True, acquire=True, release=True, name=name)


class LDUMINALB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.UMin,
                         ld=True, acquire=True, release=True, name=name)

# atomic load release


class LDADDL(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Add,
                         ld=True, acquire=False, release=True, name=name)


class LDADDLW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Add,
                         ld=True, acquire=False, release=True, name=name)


class LDADDLH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Add,
                         ld=True, acquire=False, release=True, name=name)


class LDADDLB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Add,
                         ld=True, acquire=False, release=True, name=name)


class LDCLRL(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Clr,
                         ld=True, acquire=False, release=True, name=name)


class LDCLRLW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Clr,
                         ld=True, acquire=False, release=True, name=name)


class LDCLRLH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Clr,
                         ld=True, acquire=False, release=True, name=name)


class LDCLRLB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Clr,
                         ld=True, acquire=False, release=True, name=name)


class LDEORL(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Eor,
                         ld=True, acquire=False, release=True, name=name)


class LDEORLW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Eor,
                         ld=True, acquire=False, release=True, name=name)


class LDEORLH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Eor,
                         ld=True, acquire=False, release=True, name=name)


class LDEORLB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Eor,
                         ld=True, acquire=False, release=True, name=name)


class LDSETL(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Set,
                         ld=True, acquire=False, release=True, name=name)


class LDSETLW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Set,
                         ld=True, acquire=False, release=True, name=name)


class LDSETLH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Set,
                         ld=True, acquire=False, release=True, name=name)


class LDSETLB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Set,
                         ld=True, acquire=False, release=True, name=name)


class LDMAXL(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Max,
                         ld=True, acquire=False, release=True, name=name)


class LDMAXLW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Max,
                         ld=True, acquire=False, release=True, name=name)


class LDMAXLH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Max,
                         ld=True, acquire=False, release=True, name=name)


class LDMAXLB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Max,
                         ld=True, acquire=False, release=True, name=name)


class LDMINL(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Min,
                         ld=True, acquire=False, release=True, name=name)


class LDMINLW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Min,
                         ld=True, acquire=False, release=True, name=name)


class LDMINLH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Min,
                         ld=True, acquire=False, release=True, name=name)


class LDMINLB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Min,
                         ld=True, acquire=False, release=True, name=name)


class LDUMAXL(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.UMax,
                         ld=True, acquire=False, release=True, name=name)


class LDUMAXLW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.UMax,
                         ld=True, acquire=False, release=True, name=name)


class LDUMAXLH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.UMax,
                         ld=True, acquire=False, release=True, name=name)


class LDUMAXLB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.UMax,
                         ld=True, acquire=False, release=True, name=name)


class LDUMINL(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.UMin,
                         ld=True, acquire=False, release=True, name=name)


class LDUMINLW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.UMin,
                         ld=True, acquire=False, release=True, name=name)


class LDUMINLH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.UMin,
                         ld=True, acquire=False, release=True, name=name)


class LDUMINLB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.UMin,
                         ld=True, acquire=False, release=True, name=name)

# atomic store


class STADD(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Add,
                         ld=False, acquire=False, release=False, name=name)


class STADDW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Add,
                         ld=False, acquire=False, release=False, name=name)


class STADDH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Add,
                         ld=False, acquire=False, release=False, name=name)


class STADDB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Add,
                         ld=False, acquire=False, release=False, name=name)


class STCLR(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Clr,
                         ld=False, acquire=False, release=False, name=name)


class STCLRW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Clr,
                         ld=False, acquire=False, release=False, name=name)


class STCLRH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Clr,
                         ld=False, acquire=False, release=False, name=name)


class STCLRB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Clr,
                         ld=False, acquire=False, release=False, name=name)


class STEOR(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Eor,
                         ld=False, acquire=False, release=False, name=name)


class STEORW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Eor,
                         ld=False, acquire=False, release=False, name=name)


class STEORH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Eor,
                         ld=False, acquire=False, release=False, name=name)


class STEORB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Eor,
                         ld=False, acquire=False, release=False, name=name)


class STSET(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Set,
                         ld=False, acquire=False, release=False, name=name)


class STSETW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Set,
                         ld=False, acquire=False, release=False, name=name)


class STSETH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Set,
                         ld=False, acquire=False, release=False, name=name)


class STSETB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Set,
                         ld=False, acquire=False, release=False, name=name)


class STMAX(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Max,
                         ld=False, acquire=False, release=False, name=name)


class STMAXW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Max,
                         ld=False, acquire=False, release=False, name=name)


class STMAXH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Max,
                         ld=False, acquire=False, release=False, name=name)


class STMAXB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Max,
                         ld=False, acquire=False, release=False, name=name)


class STMIN(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Min,
                         ld=False, acquire=False, release=False, name=name)


class STMINW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Min,
                         ld=False, acquire=False, release=False, name=name)


class STMINH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Min,
                         ld=False, acquire=False, release=False, name=name)


class STMINB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Min,
                         ld=False, acquire=False, release=False, name=name)


class STUMAX(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.UMax,
                         ld=False, acquire=False, release=False, name=name)


class STUMAXW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.UMax,
                         ld=False, acquire=False, release=False, name=name)


class STUMAXH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.UMax,
                         ld=False, acquire=False, release=False, name=name)


class STUMAXB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.UMax,
                         ld=False, acquire=False, release=False, name=name)


class STUMIN(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.UMin,
                         ld=False, acquire=False, release=False, name=name)


class STUMINW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.UMin,
                         ld=False, acquire=False, release=False, name=name)


class STUMINH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.UMin,
                         ld=False, acquire=False, release=False, name=name)


class STUMINB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.UMin,
                         ld=False, acquire=False, release=False, name=name)

# atomic store release


class STADDL(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Add,
                         ld=False, acquire=False, release=True, name=name)


class STADDLW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Add,
                         ld=False, acquire=False, release=True, name=name)


class STADDLH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Add,
                         ld=False, acquire=False, release=True, name=name)


class STADDLB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Add,
                         ld=False, acquire=False, release=True, name=name)


class STCLRL(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Clr,
                         ld=False, acquire=False, release=True, name=name)


class STCLRLW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Clr,
                         ld=False, acquire=False, release=True, name=name)


class STCLRLH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Clr,
                         ld=False, acquire=False, release=True, name=name)


class STCLRLB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Clr,
                         ld=False, acquire=False, release=True, name=name)


class STEORL(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Eor,
                         ld=False, acquire=False, release=True, name=name)


class STEORLW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Eor,
                         ld=False, acquire=False, release=True, name=name)


class STEORLH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Eor,
                         ld=False, acquire=False, release=True, name=name)


class STEORLB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Eor,
                         ld=False, acquire=False, release=True, name=name)


class STSETL(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Set,
                         ld=False, acquire=False, release=True, name=name)


class STSETLW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Set,
                         ld=False, acquire=False, release=True, name=name)


class STSETLH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Set,
                         ld=False, acquire=False, release=True, name=name)


class STSETLB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Set,
                         ld=False, acquire=False, release=True, name=name)


class STMAXL(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Max,
                         ld=False, acquire=False, release=True, name=name)


class STMAXLW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Max,
                         ld=False, acquire=False, release=True, name=name)


class STMAXLH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Max,
                         ld=False, acquire=False, release=True, name=name)


class STMAXLB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Max,
                         ld=False, acquire=False, release=True, name=name)


class STMINL(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.Min,
                         ld=False, acquire=False, release=True, name=name)


class STMINLW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.Min,
                         ld=False, acquire=False, release=True, name=name)


class STMINLH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.Min,
                         ld=False, acquire=False, release=True, name=name)


class STMINLB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.Min,
                         ld=False, acquire=False, release=True, name=name)


class STUMAXL(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.UMax,
                         ld=False, acquire=False, release=True, name=name)


class STUMAXLW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.UMax,
                         ld=False, acquire=False, release=True, name=name)


class STUMAXLH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.UMax,
                         ld=False, acquire=False, release=True, name=name)


class STUMAXLB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.UMax,
                         ld=False, acquire=False, release=True, name=name)


class STUMINL(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.DoubleWord, AtomicOp.UMin,
                         ld=False, acquire=False, release=True, name=name)


class STUMINLW(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Word, AtomicOp.UMin,
                         ld=False, acquire=False, release=True, name=name)


class STUMINLH(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.HalfWord, AtomicOp.UMin,
                         ld=False, acquire=False, release=True, name=name)


class STUMINLB(AtomicLDST_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, Size.Byte, AtomicOp.UMin,
                         ld=False, acquire=False, release=True, name=name)


# atomic swp
class AtomicSwp_GEN(Action):
    def __init__(self, addr: int, size: Size, acquire:bool, release:bool, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr
        self.size = size
        self.acquire = acquire
        self.release = release
    
    def Body(self):
        r = 'w'
        if self.size == Size.DoubleWord:
            r = 'x'        

        suffix = ''
        if self.acquire:
            suffix = 'a'
        if self.release:
            suffix += 'l'

        if self.size == Size.HalfWord:
            suffix = 'h'
        if self.size == Size.Byte:
            suffix = 'b'

        byte_size = self.size.ByteSize()
        bit_width = self.size.BitWidth()
        
        old_byte_val = SMReadBytes(self.addr, byte_size)
        old_int_val = int.from_bytes(old_byte_val, 'little')
        new_int_val = RandUInt(bit_width)
        new_byte_val = new_int_val.to_bytes(byte_size, 'little')
        
        SMWriteBytes(self.addr, new_byte_val)

        self.c_src = f"""
        uint{bit_width}_t ov;
        asm volatile("swp{suffix} %{r}1, %{r}0, [%2]" : "=&r"(ov) : "r" ({new_int_val:#x}), "r" ({self.addr:#x}));
        """
        self.c_src += CheckValue('ov', self.addr, old_int_val)
# swap
class SWP(AtomicSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.DoubleWord, acquire=False, release=False, name=name)

class SWPW(AtomicSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.Word, acquire=False, release=False, name=name)

class SWPH(AtomicSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.HalfWord, acquire=False, release=False, name=name)

class SWPB(AtomicSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.Byte, acquire=False, release=False, name=name)

class SWPA(AtomicSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.DoubleWord, acquire=True, release=False, name=name)

class SWPAW(AtomicSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.Word, acquire=True, release=False, name=name)

class SWPAH(AtomicSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.HalfWord, acquire=True, release=False, name=name)

class SWPAB(AtomicSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.Byte, acquire=True, release=False, name=name)

class SWPAL(AtomicSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.DoubleWord, acquire=True, release=True, name=name)

class SWPALW(AtomicSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.Word, acquire=True, release=True, name=name)

class SWPALH(AtomicSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.HalfWord, acquire=True, release=True, name=name)

class SWPALB(AtomicSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.Byte, acquire=True, release=True, name=name)

class SWPL(AtomicSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.DoubleWord, acquire=False, release=True, name=name)

class SWPLW(AtomicSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.Word, acquire=False, release=True, name=name)

class SWPLH(AtomicSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.HalfWord, acquire=False, release=True, name=name)

class SWPLB(AtomicSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.Byte, acquire=False, release=True, name=name)

# atomic cmp-swp
class AtomicCmpSwp_GEN(Action):
    def __init__(self, addr: int, size: Size, acquire:bool, release:bool, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr
        self.size = size
        self.acquire = acquire
        self.release = release
        self.cmp_eq = None
    
    def Body(self):
        r = 'w'
        if self.size == Size.DoubleWord:
            r = 'x'        

        suffix = ''
        if self.acquire:
            suffix = 'a'
        if self.release:
            suffix += 'l'

        if self.size == Size.HalfWord:
            suffix = 'h'
        if self.size == Size.Byte:
            suffix = 'b'

        byte_size = self.size.ByteSize()
        bit_width = self.size.BitWidth()
        
        old_byte_val = SMReadBytes(self.addr, byte_size)
        old_int_val = int.from_bytes(old_byte_val, 'little')
        new_int_val = RandUInt(bit_width)
        new_byte_val = new_int_val.to_bytes(byte_size, 'little')

        cmp_int_val = old_int_val

        if self.cmp_eq is None:
            self.cmp_eq = random.choice([True, False])

        if not self.cmp_eq:
            while cmp_int_val == old_int_val:
                cmp_int_val = RandUInt(bit_width)
        
        if self.cmp_eq:
            SMWriteBytes(self.addr, new_byte_val)

        self.c_src = f"""
        asm volatile("cas{suffix} %{r}0, %{r}1, [%2]" : : "r" ({cmp_int_val:#x}), "r" ({new_int_val:#x}), "r" ({self.addr:#x}));
        """

class CAS(AtomicCmpSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.DoubleWord, acquire=False, release=False, name=name)

class CASW(AtomicCmpSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.Word, acquire=False, release=False, name=name)

class CASH(AtomicCmpSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.HalfWord, acquire=False, release=False, name=name)

class CASB(AtomicCmpSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.Byte, acquire=False, release=False, name=name)

class CASA(AtomicCmpSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.DoubleWord, acquire=True, release=False, name=name)

class CASAW(AtomicCmpSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.Word, acquire=True, release=False, name=name)

class CASAH(AtomicCmpSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.HalfWord, acquire=True, release=False, name=name)

class CASAB(AtomicCmpSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.Byte, acquire=True, release=False, name=name)

class CASAL(AtomicCmpSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.DoubleWord, acquire=True, release=True, name=name)

class CASALW(AtomicCmpSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.Word, acquire=True, release=True, name=name)

class CASALH(AtomicCmpSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.HalfWord, acquire=True, release=True, name=name)

class CASALB(AtomicCmpSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.Byte, acquire=True, release=True, name=name)

class CASL(AtomicCmpSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.DoubleWord, acquire=False, release=True, name=name)

class CASLW(AtomicCmpSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.Word, acquire=False, release=True, name=name)

class CASLH(AtomicCmpSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.HalfWord, acquire=False, release=True, name=name)

class CASLB(AtomicCmpSwp_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, size=Size.Byte, acquire=False, release=True, name=name)


# compound actions
# all atomic actions are write actions

class Atomic8(Action):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Activity(self):
        addr = self.addr
        Select(
            LDADDB(addr),
            LDADDAB(addr),
            LDADDALB(addr),
            LDADDLB(addr),
            LDCLRB(addr),
            LDCLRAB(addr),
            LDCLRALB(addr),
            LDCLRLB(addr),
            LDEORB(addr),
            LDEORAB(addr),
            LDEORALB(addr),
            LDEORLB(addr),
            LDSETB(addr),
            LDSETAB(addr),
            LDSETALB(addr),
            LDSETLB(addr),
            LDMAXB(addr),
            LDMAXAB(addr),
            LDMAXALB(addr),
            LDMAXLB(addr),
            LDMINB(addr),
            LDMINAB(addr),
            LDMINALB(addr),
            LDMINLB(addr),
            LDUMAXB(addr),
            LDUMAXAB(addr),
            LDUMAXALB(addr),
            LDUMAXLB(addr),
            LDUMINB(addr),
            LDUMINAB(addr),
            LDUMINALB(addr),
            LDUMINLB(addr),

            STADDB(addr),
            STADDLB(addr),
            STCLRB(addr),
            STCLRLB(addr),
            STEORB(addr),
            STEORLB(addr),
            STSETB(addr),
            STSETLB(addr),
            STMAXB(addr),
            STMAXLB(addr),
            STMINB(addr),
            STMINLB(addr),
            STUMAXB(addr),
            STUMAXLB(addr),
            STUMINB(addr),
            STUMINLB(addr),

            SWPB(addr),
            SWPAB(addr),
            SWPALB(addr),
            SWPLB(addr),

            CASB(addr),
            CASAB(addr),
            CASALB(addr),
            CASLB(addr),
        )


class Atomic16(Action):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Activity(self):
        addr = self.addr
        Select(
            LDADDH(addr),
            LDADDAH(addr),
            LDADDALH(addr),
            LDADDLH(addr),
            LDCLRH(addr),
            LDCLRAH(addr),
            LDCLRALH(addr),
            LDCLRLH(addr),
            LDEORH(addr),
            LDEORAH(addr),
            LDEORALH(addr),
            LDEORLH(addr),
            LDSETH(addr),
            LDSETAH(addr),
            LDSETALH(addr),
            LDSETLH(addr),
            LDMAXH(addr),
            LDMAXAH(addr),
            LDMAXALH(addr),
            LDMAXLH(addr),
            LDMINH(addr),
            LDMINAH(addr),
            LDMINALH(addr),
            LDMINLH(addr),
            LDUMAXH(addr),
            LDUMAXAH(addr),
            LDUMAXALH(addr),
            LDUMAXLH(addr),
            LDUMINH(addr),
            LDUMINAH(addr),
            LDUMINALH(addr),
            LDUMINLH(addr),

            STADDH(addr),
            STADDLH(addr),
            STCLRH(addr),
            STCLRLH(addr),
            STEORH(addr),
            STEORLH(addr),
            STSETH(addr),
            STSETLH(addr),
            STMAXH(addr),
            STMAXLH(addr),
            STMINH(addr),
            STMINLH(addr),
            STUMAXH(addr),
            STUMAXLH(addr),
            STUMINH(addr),
            STUMINLH(addr),

            SWPH(addr),
            SWPAH(addr),
            SWPALH(addr),
            SWPLH(addr),

            CASH(addr),
            CASAH(addr),
            CASALH(addr),
            CASLH(addr),
        )


class Atomic32(Action):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Activity(self):
        addr = self.addr
        Select(
            LDADDW(addr),
            LDADDAW(addr),
            LDADDALW(addr),
            LDADDLW(addr),
            LDCLRW(addr),
            LDCLRAW(addr),
            LDCLRALW(addr),
            LDCLRLW(addr),
            LDEORW(addr),
            LDEORAW(addr),
            LDEORALW(addr),
            LDEORLW(addr),
            LDSETW(addr),
            LDSETAW(addr),
            LDSETALW(addr),
            LDSETLW(addr),
            LDMAXW(addr),
            LDMAXAW(addr),
            LDMAXALW(addr),
            LDMAXLW(addr),
            LDMINW(addr),
            LDMINAW(addr),
            LDMINALW(addr),
            LDMINLW(addr),
            LDUMAXW(addr),
            LDUMAXAW(addr),
            LDUMAXALW(addr),
            LDUMAXLW(addr),
            LDUMINW(addr),
            LDUMINAW(addr),
            LDUMINALW(addr),
            LDUMINLW(addr),

            STADDW(addr),
            STADDLW(addr),
            STCLRW(addr),
            STCLRLW(addr),
            STEORW(addr),
            STEORLW(addr),
            STSETW(addr),
            STSETLW(addr),
            STMAXW(addr),
            STMAXLW(addr),
            STMINW(addr),
            STMINLW(addr),
            STUMAXW(addr),
            STUMAXLW(addr),
            STUMINW(addr),
            STUMINLW(addr),

            SWPW(addr),
            SWPAW(addr),
            SWPALW(addr),
            SWPLW(addr),

            CASW(addr),
            CASAW(addr),
            CASALW(addr),
            CASLW(addr),
        )


class Atomic64(Action):
    def __init__(self, addr: int,  name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Activity(self):
        addr = self.addr
        Select(
            LDADD(addr),
            LDADDA(addr),
            LDADDAL(addr),
            LDADDL(addr),
            LDCLR(addr),
            LDCLRA(addr),
            LDCLRAL(addr),
            LDCLRL(addr),
            LDEOR(addr),
            LDEORA(addr),
            LDEORAL(addr),
            LDEORL(addr),
            LDSET(addr),
            LDSETA(addr),
            LDSETAL(addr),
            LDSETL(addr),
            LDMAX(addr),
            LDMAXA(addr),
            LDMAXAL(addr),
            LDMAXL(addr),
            LDMIN(addr),
            LDMINA(addr),
            LDMINAL(addr),
            LDMINL(addr),
            LDUMAX(addr),
            LDUMAXA(addr),
            LDUMAXAL(addr),
            LDUMAXL(addr),
            LDUMIN(addr),
            LDUMINA(addr),
            LDUMINAL(addr),
            LDUMINL(addr),

            STADD(addr),
            STADDL(addr),
            STCLR(addr),
            STCLRL(addr),
            STEOR(addr),
            STEORL(addr),
            STSET(addr),
            STSETL(addr),
            STMAX(addr),
            STMAXL(addr),
            STMIN(addr),
            STMINL(addr),
            STUMAX(addr),
            STUMAXL(addr),
            STUMIN(addr),
            STUMINL(addr),

            SWP(addr),
            SWPA(addr),
            SWPAL(addr),
            SWPL(addr),

            CAS(addr),
            CASA(addr),
            CASAL(addr),
            CASL(addr),
        )

# read write interface


class Read8(Action):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Activity(self):
        Select(LDRB(self.addr),
               LDXRB(self.addr),
               LDARB(self.addr),
               LDLARB(self.addr))


class Read16(Action):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Activity(self):
        Select(LDRH(self.addr),
               LDXRH(self.addr),
               LDARH(self.addr),
               LDLARH(self.addr))


class Read32(Action):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Activity(self):
        Select(LDRW(self.addr),
               LDXRW(self.addr),
               LDARW(self.addr),
               LDLARW(self.addr))


class Read64(Action):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Activity(self):
        Select(LDR(self.addr),
               LDXR(self.addr),
               LDAR(self.addr),
               LDLAR(self.addr))


class Read128(Action):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Activity(self):
        Select(LDP(self.addr),
               LDNP(self.addr),
               LDXP(self.addr))


class Write8(Action):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Activity(self):
        Select(
            STRB(self.addr),
            STXRB(self.addr),
            STLRB(self.addr),
            STLLRB(self.addr),
            Atomic8(self.addr),
        )


class Write16(Action):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Activity(self):
        Select(
            STRH(self.addr),
            STXRH(self.addr),
            STLRH(self.addr),
            STLLRH(self.addr),
            Atomic16(self.addr),
        )


class Write32(Action):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Activity(self):
        Select(
            STRW(self.addr),
            STXRW(self.addr),
            STLRW(self.addr),
            STLLRW(self.addr),
            Atomic32(self.addr)
        )


class Write64(Action):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Activity(self):
        Select(
            STR(self.addr),
            STXR(self.addr),
            STLR(self.addr),
            STLLR(self.addr),
            Atomic64(self.addr),
        )


class Write128(Action):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Activity(self):
        Select(
               STP(self.addr),
               STNP(self.addr),
               STXP(self.addr),
            )


class Read(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        size = random.randrange(0, 5)
        # size = 4
        match size:
            case 0:
                offset = random.randrange(0, MEMCELL_SIZE)
                Do(Read8(self.cl.addr+offset))
            case 1:
                offset = random.randrange(0, MEMCELL_SIZE//2)
                offset *= 2
                Do(Read16(self.cl.addr+offset))
            case 2:
                offset = random.randrange(0, MEMCELL_SIZE//4)
                offset *= 4
                Do(Read32(self.cl.addr+offset))
            case 3:
                offset = random.randrange(0, MEMCELL_SIZE//8)
                offset *= 8
                Do(Read64(self.cl.addr+offset))
            case 4:
                assert (MEMCELL_SIZE >= 16)
                offset = random.randrange(0, MEMCELL_SIZE//16)
                offset *= 16
                Do(Read128(self.cl.addr+offset))


class Write(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        size = random.randrange(0, 5)
        # size = 3
        match size:
            case 0:
                offset = random.randrange(0, MEMCELL_SIZE)
                Do(Write8(self.cl.addr+offset))
            case 1:
                offset = random.randrange(0, MEMCELL_SIZE//2)
                offset *= 2
                Do(Write16(self.cl.addr+offset))
            case 2:
                offset = random.randrange(0, MEMCELL_SIZE//4)
                offset *= 4
                Do(Write32(self.cl.addr+offset))
            case 3:
                offset = random.randrange(0, MEMCELL_SIZE//8)
                offset *= 8
                Do(Write64(self.cl.addr+offset))
            case 4:
                offset = random.randrange(0, MEMCELL_SIZE//16)
                offset *= 16
                Do(Write128(self.cl.addr+offset))

class WriteNoAlloc(Write):
    pass

# data cache maintanance
class DCVA_GEN(Action):
    def __init__(self, addr:int, inst: str, name: str = None) -> None:
        super().__init__(name)
        assert(addr%64 == 0)
        self.addr = addr
        self.inst = inst

    def Body(self):
        self.c_src = f'asm volatile("{self.inst}, %x0" : : "r" ({self.addr:#x}));'

class DCIVAC(DCVA_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, 'dc ivac', name)

class DCCVAC(DCVA_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, 'dc cvac', name)

class DCCVAU(DCVA_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, 'dc cvau', name)

class DCCVAP(DCVA_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, 'dc cvap', name)

class DCCIVAC(DCVA_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, 'dc civac', name)

class DCZVA(DCVA_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, 'dc zva', name)
    
    def Body(self):
        super().Body()
        SMWriteBytes(self.addr, bytes(CACHELINE_SIZE))

class DCSW_GEN(Action):
    def __init__(self, addr:int, inst: str, name: str = None) -> None:
        super().__init__(name)
        assert(addr%64 == 0)
        self.addr = addr
        self.inst = inst

    def Body(self):
        self.c_src = f"""
        asm_volatile(
        
        )
        """

# Cache maintainence instructions that operate on VA must effect the caches of other PEs in the same shareability domain.
# The IC IALLU and DC set/way instructions apply only to the PE that performs the instructions.

# class DCISW(DCSW_GEN):
#     def __init__(self, addr: int, name: str = None) -> None:
#         super().__init__(addr, 'dc isw', name)

class DCCSW(DCSW_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, 'dc csw', name)

    def Body(self) -> None:
        self.c_src = f'dc_csw({self.addr:#x});'

class DCCISW(DCSW_GEN):
    def __init__(self, addr: int, name: str = None) -> None:
        super().__init__(addr, 'dc cisw', name)

    def Body(self) -> None:
        self.c_src = f'dc_cisw({self.addr:#x});'

class Clean(Action):
    def __init__(self, cl:Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(DCCSW(self.cl.aligned_addr))

class CleanInvalidate(Action):
    def __init__(self, cl:Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl
    
    def Activity(self):
        Do(DCCISW(self.cl.aligned_addr))

class CleanDomain(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl
    
    def Activity(self):
        addr = self.cl.aligned_addr
        # invalidate 操作暂时无法支持，不能丢失 modified 的值
        Select(
            DCCVAC(addr),
            DCCVAP(addr),
            DCCVAU(addr),
        )

class CleanInvalidateDomain(Action):
    def __init__(self, cl:Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        addr = self.cl.aligned_addr
        Select(
            DCCIVAC(addr),
            DCZVA(addr),
        )

class Init(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Body(self):
        value = bytearray(MEMCELL_SIZE)
        for i in range(MEMCELL_SIZE):
            value[i] = random.randrange(0, 256)
        SMWriteBytes(self.cl.addr, value)

        self.c_src = ''
        for i in range(MEMCELL_SIZE//8):
            offset = i*8
            addr = self.cl.addr+offset
            v = int.from_bytes(value[offset:offset+8], 'little')
            self.c_src += f'asm volatile("str %x1, [%0]" : : "r" ({addr:#x}), "r" ({v:#x}));\n'


# 不要超过组相联数量，因为本测试的目标是测试 cacheline 的状态转换，而不是测试替换能力
# 并且超过组相联约束会破坏状态转换

class CachelinePool:
    def __init__(self) -> None:
        self.addr_space = AddrSpace()

    def Alloc(self) -> Cacheline:
        # logger.info(f'cl allocation begins')
        cl = Cacheline()
        # 分配 cacheline 尺寸，随机使用其中 MEMSIZE
        cl.aligned_addr = self.addr_space.AllocRandom(
            CACHELINE_SIZE, CACHELINE_SIZE)
        cl.addr = cl.aligned_addr + MEMCELL_SIZE * \
            random.randrange(0, CACHELINE_SIZE//MEMCELL_SIZE)
        # logger.info(f'cl allocation ends with addr: 0x{cl.addr:x}')
        return cl

    def Free(self, cl: Cacheline) -> None:
        # logger.debug(f'cl free begins with addr: 0x{cl.addr:x}')
        self.addr_space.Free(cl.aligned_addr, CACHELINE_SIZE)
        # logger.debug(f'cl free ends')

AARCH64_DECL = r"""
#define ID_MMFR2_CCIDX_SHIFT (20)
#define ID_MMFR2_CCIDX_MASK (0xF)

uint64_t associativity;
uint64_t num_sets;
uint64_t assoc_shift;
uint64_t index_mask;

static void dc_init() {
  uint64_t id_mmfr2;
  asm volatile("mrs %x0, id_aa64mmfr2_el1" : "=&r"(id_mmfr2) :);
  uint64_t id_mmfr2_ccidx =
      ((id_mmfr2 >> ID_MMFR2_CCIDX_SHIFT) & ID_MMFR2_CCIDX_MASK);

  uint64_t ccsidr_assoc_shift;
  uint64_t ccsidr_assoc_mask;
  uint64_t ccsidr_nsets_shift;
  uint64_t ccsidr_nests_mask;

  if (id_mmfr2_ccidx == 0) {
    // 3,10
    ccsidr_assoc_shift = 3;
    ccsidr_assoc_mask = 0x3FF;
    // 13,15
    ccsidr_nsets_shift = 13;
    ccsidr_nests_mask = 0x7FFF;
  } else {
    // 3,21
    ccsidr_assoc_shift = 3;
    ccsidr_assoc_mask = 0x1FFFFF;
    // 32,24
    ccsidr_nsets_shift = 32;
    ccsidr_nests_mask = 0xFFFFFF;
  }

  asm volatile("msr csselr_el1, %x0" ::"r"(0));
  uint64_t ccsidr;
  asm volatile("mrs %x0, ccsidr_el1" : "=&r"(ccsidr) :);
  //   printf("ccsidr: %x\n", ccsidr);
  associativity = ((ccsidr >> ccsidr_assoc_shift) & ccsidr_assoc_mask) + 1;
  num_sets = ((ccsidr >> ccsidr_nsets_shift) & ccsidr_nests_mask) + 1;
  //   printf("assoc: %d, nsets: %d\n", associativity, num_sets);

  assoc_shift = 0;
  ccsidr = associativity - 1;
  while (ccsidr != 0) {
    ccsidr = (ccsidr >> 1);
    assoc_shift += 1;
  }
  assoc_shift = 32 - assoc_shift;
  //   printf("assoc shift: %d\n", assoc_shift);

  ccsidr = num_sets - 1;
  index_mask = 0;
  while (ccsidr != 0) {
    ccsidr = (ccsidr >> 1);
    index_mask += 1;
  }
  index_mask = index_mask + 6;
  index_mask = (1 << index_mask);
  index_mask = (index_mask - 1) & (~0x3F);
  //   printf("index mask: %x\n", index_mask);
}

static void dc_csw(uint64_t addr) {
  for (uint64_t way = 0; way < associativity; way++) {
    uint64_t sw = (addr & index_mask);
    sw |= (way << assoc_shift);
    asm volatile("dc csw, %x0" ::"r"(sw));
  }
}

static void dc_cisw(uint64_t addr) {
  for (uint64_t way = 0; way < associativity; way++) {
    uint64_t sw = (addr & index_mask);
    sw |= (way << assoc_shift);
    asm volatile("dc cisw, %x0" ::"r"(sw));
  }
}
"""

class AArch64Init(Action):
    def __init__(self, name: str = None) -> None:
        super().__init__(name)

    def Body(self) -> None:
        self.c_src = "dc_init();"

class AArch64Moesi(Action):
    def __init__(self, npt: int, name: str = None) -> None:
        super().__init__(name)
        self.npt = npt
        self.c_headers = ['#include "print.h"', '#include "xrt.h"']
        self.c_decl = AARCH64_DECL

    def Activity(self) -> None:
        Do(AArch64Init())
        Do(moesi.MoesiTest(self.npt))


def Main():
    logging.basicConfig(level=logging.INFO)

    cl_pool = CachelinePool()

    for fr in ivy_app_cfg.FREE_RANGES:
        logger.info(f'addr space region: {fr[0]:#x}, {fr[1]:#x}')
        cl_pool.addr_space.AddNode(fr[0], fr[1]-fr[0]+1, fr[2])

    moesi.cacheline_pool = cl_pool

    parser = argparse.ArgumentParser()
    purslane.dsl.PrepareArgParser(parser)

    # parser.add_argument('--num_parallel', type=int, default=None)
    # parser.add_argument('--max_num_state_change', type=int, default=30)
    parser.add_argument('--num_repeat_times', type=int, default=2)

    args = parser.parse_args()
    args.num_executors = ivy_app_cfg.NR_CPUS

    if args.num_executors < 2:
        raise ('need more than one executor')

    num_repeat_times = args.num_repeat_times

    num_repeat_times = 64

    moesi.NUM_EXECUTORS = args.num_executors
    moesi.MAX_NUM_PARALLEL = 1
    # moesi.NUM_EXECUTORS * 4
    moesi.MIN_NUM_PARALLEL = 1
    # moesi.NUM_EXECUTORS * 1

    with (TypeOverride(moesi.Init, Init),
          TypeOverride(moesi.Read, Read),
          TypeOverride(moesi.Write, Write),
          TypeOverride(moesi.WriteNoAlloc, WriteNoAlloc),
          TypeOverride(moesi.Clean, Clean),
          TypeOverride(moesi.CleanInvalidate, CleanInvalidate),
          TypeOverride(moesi.CleanDomain, CleanDomain),
          TypeOverride(moesi.CleanInvalidateDomain, CleanInvalidateDomain)):
        Run(AArch64Moesi(num_repeat_times), args)


if __name__ == '__main__':
    Main()
