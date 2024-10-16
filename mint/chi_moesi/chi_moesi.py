import random
import logging
import argparse

from enum import Enum

# from . import moesi
from mint import moesi
from mint.models.moesi import Cacheline
import purslane
from purslane.dsl import Do, Action, Sequence, Parallel, Select, Run, TypeOverride
from purslane.dsl import RandU8, RandU16, RandU32, RandU64, RandUInt, RandS8, RandS16, RandS32, RandS64, RandInt, RandBytes
from purslane.addr_space import AddrSpace
from purslane.addr_space import SMWrite8, SMWrite16, SMWrite32, SMWrite64, SMWriteBytes
from purslane.addr_space import SMRead8, SMRead16, SMRead32, SMRead64, SMReadBytes

logger = logging.getLogger('chi_moesi')


def BytesSvStr(ba: bytearray) -> str:
    ss = [f'8\'h{b:x}' for b in ba]
    sj = ','.join(ss)
    return '{'+sj+'}'


def RandomCacheValue(num: int = 64) -> bytes:
    rba = bytearray(num)
    for i in range(num):
        v = random.randrange(0, 256)
        rba[i] = v
    return bytes(rba)


CACHELINE_SIZE = 64

# Read
class ReadClean(Action):
    def __init__(self, addr:int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Body(self):
        bv = BytesSvStr(SMReadBytes(self.addr, CACHELINE_SIZE))
        self.sv_src = f'exec.ReadClean(64\'h{self.addr:x}, {bv});'


class ReadNotSharedDirty(Action):
    def __init__(self, addr:int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Body(self):
        bv = BytesSvStr(SMReadBytes(self.addr, CACHELINE_SIZE))
        self.sv_src = f'exec.ReadNotSharedDirty(64\'h{self.addr:x}, {bv});'


class ReadShared(Action):
    def __init__(self, addr:int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Body(self):
        bv = BytesSvStr(SMReadBytes(self.addr, CACHELINE_SIZE))
        self.sv_src = f'exec.ReadShared(64\'h{self.addr:x}, {bv});'


class ReadUnique(Action):
    def __init__(self, addr:int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Body(self):
        bv = BytesSvStr(SMReadBytes(self.addr, CACHELINE_SIZE))
        self.sv_src = f'exec.ReadUnique(64\'h{self.addr:x}, {bv});'


# class ReadPreferUnique(Action):
#     def Body(self):
#         assert (self.cl.value is not None)
#         self.sv_src = f'exec.ReadPreferUnique(64\'h{self.cl.addr:x}, {self.cl.ValueSvStr()});'

# Write
class Modify(Action):
    def __init__(self, addr:int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Body(self):
        v = RandBytes(CACHELINE_SIZE)
        bv = BytesSvStr(v)
        # with readunique/makeunique
        self.sv_src = f'exec.Modify(64\'h{self.addr:x}, {bv});'
        SMWriteBytes(self.addr, v)

class WriteUniqueFull(Action):
    def __init__(self, addr: int,name: str = None) -> None:
        super().__init__(name)
        self.addr =addr

    def Body(self):
        v = RandBytes(CACHELINE_SIZE)
        bv = BytesSvStr(v)
        self.sv_src = f'exec.WriteUniqueFull(64\'h{self.addr:x}, {bv});'
        SMWriteBytes(self.addr, v)


class WriteCleanFull(Action):
    def __init__(self, addr: int,name: str = None) -> None:
        super().__init__(name)
        self.addr =addr

    def Body(self):
        self.sv_src = f'exec.WriteCleanFull(64\'h{self.addr:x});'

class SafeEvict(Action):
    def __init__(self, addr:int, name: str = None) -> None:
        super().__init__(name)
        self.addr =addr

    def Body(self):
        self.sv_src = f'exec.SafeEvict(64\'h{self.addr:x});'


# cmo
# CleanShared
# CleanInvalid
# MakeInvalid
class CleanShared(Action):
    def __init__(self, addr:int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Body(self):
        self.sv_src = f'exec.CleanShared(64\'h{self.addr:x});'

# class CleanSharedPersist(RequestAction):
#   def Body(self):
#     pass


class CleanInvalid(Action):
    def __init__(self, addr:int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Body(self):
        self.sv_src = f'exec.CleanInvalid(64\'h{self.addr:x});'

# 丢弃 dirty 副本，暂时无法测试，因为丢弃以后，无法检查后续值是否正确
# 需要记住上次写回的值


class MakeInvalid(Action):
    def __init__(self, addr:int,name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Body(self):
        self.sv_src = f'exec.MakeInvalid(64\'h{self.addr:x});'


# atomic
class AtomicLSOp(Enum):
    ADD = 0
    CLR = 1
    EOR = 2
    SET = 3
    SMAX = 4
    SMIN = 5
    UMAX = 6
    UMIN = 7

    # DENALI_CHI_REQOPCODE_AtomicStore_ADD,
    # DENALI_CHI_REQOPCODE_AtomicStore_CLR,
    # DENALI_CHI_REQOPCODE_AtomicStore_EOR,
    # DENALI_CHI_REQOPCODE_AtomicStore_SET,
    # DENALI_CHI_REQOPCODE_AtomicStore_SMAX,
    # DENALI_CHI_REQOPCODE_AtomicStore_SMIN,
    # DENALI_CHI_REQOPCODE_AtomicStore_UMAX,
    # DENALI_CHI_REQOPCODE_AtomicStore_UMIN,
    # DENALI_CHI_REQOPCODE_AtomicLoad_ADD,
    # DENALI_CHI_REQOPCODE_AtomicLoad_CLR,
    # DENALI_CHI_REQOPCODE_AtomicLoad_EOR,
    # DENALI_CHI_REQOPCODE_AtomicLoad_SET,
    # DENALI_CHI_REQOPCODE_AtomicLoad_SMAX,
    # DENALI_CHI_REQOPCODE_AtomicLoad_SMIN,
    # DENALI_CHI_REQOPCODE_AtomicLoad_UMAX,
    # DENALI_CHI_REQOPCODE_AtomicLoad_UMIN,


def CdnChiAtomicOpcode(op: AtomicLSOp) -> str:
    match op:
        case AtomicLSOp.ADD:
            return 'ADD'
        case AtomicLSOp.CLR:
            return 'CLR'
        case AtomicLSOp.EOR:
            return 'EOR'
        case AtomicLSOp.SET:
            return 'SET'
        case AtomicLSOp.SMAX:
            return 'SMAX'
        case AtomicLSOp.SMIN:
            return 'SMIN'
        case AtomicLSOp.UMAX:
            return 'UMAX'
        case AtomicLSOp.UMIN:
            return 'UMIN'


def CdnChiAtomicLoadOpcode(op: AtomicLSOp) -> str:
    return 'DENALI_CHI_REQOPCODE_AtomicLoad_'+CdnChiAtomicOpcode(op)


def CdnChiAtomicStoreOpcode(op: AtomicLSOp) -> str:
    return 'DENALI_CHI_REQOPCODE_AtomicStore_'+CdnChiAtomicOpcode(op)


def AtomicADD(init_val: bytearray, txn_val: bytearray) -> bytearray:
    size = len(init_val)
    mask = 0
    match size:
        case 1:
            mask = 0xFF
        case 2:
            mask = 0xFFFF
        case 4:
            mask = 0xFFFFFFFF
        case 8:
            mask = 0xFFFFFFFFFFFFFFFF

    iv = int.from_bytes(init_val, 'little')
    tv = int.from_bytes(txn_val, 'little')
    rv = (iv + tv)
    rv = rv & mask
    return bytearray(rv.to_bytes(size, 'little'))


def AtomicCLR(init_val: bytearray, txn_val: bytearray) -> bytearray:
    return bytearray([iv & ((~tv) & 0xFF) for iv, tv in zip(init_val, txn_val)])


def AtomicEOR(init_val: bytearray, txn_val: bytearray) -> bytearray:
    return bytearray([iv ^ tv for iv, tv in zip(init_val, txn_val)])


def AtomicSET(init_val: bytearray, txn_val: bytearray) -> bytearray:
    return bytearray([iv | tv for iv, tv in zip(init_val, txn_val)])


def AtomicSMAX(init_val: bytearray, txn_val: bytearray) -> bytearray:
    iv = int.from_bytes(init_val, 'little', signed=True)
    tv = int.from_bytes(txn_val, 'little', signed=True)
    if tv > iv:
        return bytearray(txn_val)
    else:
        return bytearray(init_val)


def AtomicSMIN(init_val: bytearray, txn_val: bytearray) -> bytearray:
    iv = int.from_bytes(init_val, 'little', signed=True)
    tv = int.from_bytes(txn_val, 'little', signed=True)
    if tv < iv:
        return bytearray(txn_val)
    else:
        return bytearray(init_val)


def AtomicUMAX(init_val: bytearray, txn_val: bytearray) -> bytearray:
    iv = int.from_bytes(init_val, 'little', signed=False)
    tv = int.from_bytes(txn_val, 'little', signed=False)
    if tv > iv:
        return bytearray(txn_val)
    else:
        return bytearray(init_val)


def AtomicUMIN(init_val: bytearray, txn_val: bytearray) -> bytearray:
    iv = int.from_bytes(init_val, 'little', signed=False)
    tv = int.from_bytes(txn_val, 'little', signed=False)
    if tv < iv:
        return bytearray(txn_val)
    else:
        return bytearray(init_val)

# @vsc.randobj


class AtomicLoadStoreOps:
    def __init__(self, init_cl_value: bytearray) -> None:
        self.init_cl_value = bytearray(init_cl_value)
        self.updated_cl_value = bytearray(init_cl_value)
        self.init_value: bytearray = None
        self.txn_value: bytearray = None
        self.op = AtomicLSOp.ADD
        self.size = 0
        self.offset = 0

        # self.op = vsc.rand_enum_t(AtomicLSOp)
        # self.size = vsc.rand_bit_t(8)
        # self.offset = vsc.rand_bit_t(8)

    # @vsc.constraint
    # def cons(self):
    #   self.offset <= 63
    #   self.size in vsc.rangelist(1,2,4,8)
    #   (self.offset % self.size) == 0
    #   vsc.solve_order(self.size, self.offset)

    def Randomize(self):
        size_shift = random.randrange(0, 4)
        self.size = (1 << size_shift)
        self.offset = random.randrange(0, 64)
        self.offset = (self.offset // self.size) * self.size
        self.op = AtomicLSOp(random.randrange(0, 8))

        self.post_randomize()

    def post_randomize(self):
        lo = self.offset
        hi = self.offset + self.size
        self.txn_value = RandBytes(self.size)
        self.init_value = bytearray(self.init_cl_value[lo:hi])

        new_value = None
        match self.op:
            case AtomicLSOp.ADD:
                new_value = AtomicADD(self.init_value, self.txn_value)
            case AtomicLSOp.CLR:
                new_value = AtomicCLR(self.init_value, self.txn_value)
            case AtomicLSOp.EOR:
                new_value = AtomicEOR(self.init_value, self.txn_value)
            case AtomicLSOp.SET:
                new_value = AtomicSET(self.init_value, self.txn_value)
            case AtomicLSOp.SMAX:
                new_value = AtomicSMAX(self.init_value, self.txn_value)
            case AtomicLSOp.SMIN:
                new_value = AtomicSMIN(self.init_value, self.txn_value)
            case AtomicLSOp.UMAX:
                new_value = AtomicUMAX(self.init_value, self.txn_value)
            case AtomicLSOp.UMIN:
                new_value = AtomicUMIN(self.init_value, self.txn_value)

        self.updated_cl_value[lo:hi] = new_value


class AtomicLoad(Action):
    def __init__(self, addr:int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Body(self):
        init_value = SMReadBytes(self.addr, CACHELINE_SIZE)
        aso = AtomicLoadStoreOps(init_value)
        aso.Randomize()
        self.sv_src = f'exec.AtomicLoad(64\'h{self.addr:x}, {BytesSvStr(aso.init_value)}, {BytesSvStr(aso.txn_value)}, 8\'d{aso.offset}, 8\'d{aso.size}, {CdnChiAtomicLoadOpcode(aso.op)});'
        SMWriteBytes(self.addr, aso.updated_cl_value)


class AtomicStore(Action):
    def __init__(self, addr:int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Body(self):
        init_value = SMReadBytes(self.addr, CACHELINE_SIZE)
        aso = AtomicLoadStoreOps(init_value)
        aso.Randomize()
        self.sv_src = f'exec.AtomicStore(64\'h{self.addr:x}, {BytesSvStr(aso.txn_value)}, 8\'d{aso.offset}, 8\'d{aso.size}, {CdnChiAtomicStoreOpcode(aso.op)});'
        SMWriteBytes(self.addr, aso.updated_cl_value)


class AtomicSwapOps:
    def __init__(self, init_value: bytearray) -> None:
        self.init_cl_value = bytearray(init_value)
        self.updated_cl_value = bytearray(init_value)
        self.init_value: bytearray = None
        self.swap_value: bytearray = None
        self.size = 0
        self.offset = 0

        # self.size = vsc.rand_bit_t(8)
        # self.offset = vsc.rand_bit_t(8)

    # @vsc.constraint
    # def cons(self):
    #   self.offset <= 63
    #   self.size in vsc.rangelist(1,2,4,8)
    #   (self.offset % self.size) == 0
    #   vsc.solve_order(self.size, self.offset)

    # pyvsc 太慢了
    def Randomize(self):
        self.size = random.randrange(0, 4)
        self.size = (1 << self.size)
        self.offset = random.randrange(0, 64)
        # align
        self.offset = (self.offset//self.size) * self.size
        self.post_randomize()

    def post_randomize(self):
        lo = self.offset
        hi = self.offset + self.size
        self.swap_value = RandBytes(self.size)
        self.init_value = bytearray(self.init_cl_value[lo:hi])
        self.updated_cl_value[lo:hi] = self.swap_value


class AtomicSwap(Action):
    def __init__(self, addr:int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Body(self):
        init_value = SMReadBytes(self.addr, CACHELINE_SIZE)
        aso = AtomicSwapOps(init_value)
        aso.Randomize()
        self.sv_src = f'exec.AtomicSwap(64\'h{self.addr:x}, {BytesSvStr(aso.init_value)}, {BytesSvStr(aso.swap_value)}, 8\'d{aso.offset}, 8\'d{aso.size});'
        SMWriteBytes(self.addr, aso.updated_cl_value)

# @vsc.randobj


class AtomicCompareOps:
    def __init__(self, init_value: bytearray) -> None:
        self.init_cl_value = bytearray(init_value)
        self.updated_cl_value = bytearray(init_value)
        self.init_value: bytearray = None
        self.cmp_value: bytearray = None
        self.swap_value: bytearray = None

        self.size = 0
        self.offset = 0
        self.match = False

        # self.size = vsc.rand_bit_t(8)
        # self.offset = vsc.rand_bit_t(8)
        # self.match = vsc.rand_bit_t(1)

    # @vsc.constraint
    # def cons(self):
    #   self.offset <= 63
    #   self.size in vsc.rangelist(1,2,4,8,16)
    #   (self.offset % self.size) == 0
    #   vsc.solve_order(self.size, self.offset)

    def Randomize(self):
        size_shift = random.randrange(0, 5)
        self.size = (1 << size_shift)
        self.offset = random.randrange(0, CACHELINE_SIZE)
        self.offset = (self.offset // self.size) * self.size
        is_match = random.randrange(0, 2)
        if is_match == 1:
            self.match = True
        else:
            self.match = False

        self.post_randomize()

    def post_randomize(self):
        lo = self.offset
        hi = self.offset + self.size
        self.init_value = bytearray(self.init_cl_value[lo:hi])
        self.swap_value = RandBytes(self.size)

        if self.match == 1:
            self.cmp_value = bytearray(self.init_value)
            self.updated_cl_value[lo:hi] = self.swap_value
        else:
            self.cmp_value = bytearray(self.init_value)
            self.cmp_value[0] = (self.cmp_value[0] + 1) & 0xFF


class AtomicCompare(Action):
    def __init__(self, addr:int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Body(self):
        init_value = SMReadBytes(self.addr, CACHELINE_SIZE)
        aso = AtomicCompareOps(init_value)
        aso.Randomize()
        self.sv_src = f'exec.AtomicCompare(64\'h{self.addr:x}, {BytesSvStr(aso.init_value)}, {BytesSvStr(aso.cmp_value)}, {BytesSvStr(aso.swap_value)}, 8\'d{aso.offset}, 8\'d{aso.size});'
        SMWriteBytes(self.addr, aso.updated_cl_value)

class AtomicAction(Action):
    def __init__(self, addr:int, name: str = None) -> None:
        super().__init__(name)
        self.addr = addr

    def Activity(self):
        Select(
               AtomicLoad(self.addr),
               AtomicStore(self.addr),
               AtomicSwap(self.addr),
               AtomicCompare(self.addr)
            )

# action interface implementation
class Init(Action):
    def __init__(self, cl:Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Modify(self.cl.addr))

class Read(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(
            ReadClean(self.cl.addr),
            ReadNotSharedDirty(self.cl.addr),
            ReadShared(self.cl.addr),
            ReadUnique(self.cl.addr)
        )


class Write(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Modify(self.cl.addr))

class WriteNoAlloc(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(
            AtomicAction(self.cl.addr),
            WriteUniqueFull(self.cl.addr),
        )

class Clean(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(WriteCleanFull(self.cl.addr))

class CleanInvalidate(Action):
    def __init__(self, cl:Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(SafeEvict(self.cl.addr))

class CleanDomain(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(CleanShared(self.cl.addr))

class CleanInvalidateDomain(Action):
    def __init__(self, cl:Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(CleanInvalid(self.cl.addr))

class CachelinePool:
    def __init__(self) -> None:
        self.addr_space = AddrSpace()

    def Alloc(self) -> Cacheline:
        cl = Cacheline()
        cl.addr = self.addr_space.AllocRandom(
            CACHELINE_SIZE, CACHELINE_SIZE)
        return cl

    def Free(self, cl: Cacheline) -> None:
        self.addr_space.Free(cl.addr, CACHELINE_SIZE)


def Main():
    # logging.basicConfig(filename='build/myapp.log', filemode='w', level=logging.INFO)
    logging.basicConfig(level=logging.INFO)

    cl_pool = CachelinePool()
    cl_pool.addr_space.Add(0x17000000000, 0x10000000)
    moesi.cacheline_pool = cl_pool

    parser = argparse.ArgumentParser()
    purslane.dsl.PrepareArgParser(parser)

    # parser.add_argument('--num_parallel', type=int, default=None)
    # parser.add_argument('--max_num_state_change', type=int, default=30)
    parser.add_argument('--num_repeat_times', type=int, default=2)

    args = parser.parse_args()

    if args.seed is not None:
        rand_seed = args.seed
    else:
        rand_seed = random.getrandbits(31)
    random.seed(rand_seed)
    logger.info(f'random seed is {rand_seed}')

    if args.num_executors < 2:
        raise ('need more than one executor')

    num_repeat_times = args.num_repeat_times

    moesi.NUM_EXECUTORS = args.num_executors
    moesi.MAX_NUM_PARALLEL = moesi.NUM_EXECUTORS * 64
    moesi.MIN_NUM_PARALLEL = moesi.NUM_EXECUTORS * 16

    # moesi.MIN_NUM_PARALLEL = 1
    # moesi.MAX_NUM_PARALLEL = 1

    with (TypeOverride(moesi.Init, Init),
          TypeOverride(moesi.Read, Read),
          TypeOverride(moesi.Write, Write),
          TypeOverride(moesi.WriteNoAlloc, WriteNoAlloc),
          TypeOverride(moesi.Clean, Clean),
          TypeOverride(moesi.CleanInvalidate, CleanInvalidate),
          TypeOverride(moesi.CleanDomain, CleanDomain),
          TypeOverride(moesi.CleanInvalidateDomain, CleanInvalidateDomain)):
        Run(moesi.MoesiTest(num_repeat_times), args)

if __name__ == '__main__':
    Main()
