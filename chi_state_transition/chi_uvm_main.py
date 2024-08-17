import random
import argparse
import logging
import typing
# import state
import vsc
from dataclasses import dataclass
from enum import Enum

import purslane.dsl
import purslane.state
from purslane.dsl import Do, Action, Sequence, Parallel, Select, Run, TypeOverride
from purslane.state import StateTransition, StateInfer

logger = logging.getLogger(__name__)

# modify manully according to the testbench
SnoopableAddrRange = [
]

# uvm 环境 dut 是一个 chi-noc
# 检查其是否在外部 rnf cacheline 状态转移时是否可以正确工作
# 有些状态转换只在 rnf 内部发生所以不产生影响，例如
# UniqueDirtyToUniqueDirty
# UniqueCleanToUniqueClean
# SharedCleanToSharedClean(来自本地 rnf 的访问)
# SharedDirtyToSharedDirty(来自本地 rnf 的访问)

# 这四者在使用 c/asm 进行测试时是有含义的，因为 dut 是处理器+noc
# 同时测试 rnf（处理核）+ noc 能够在各种状态转移是否可以正确工作

NUM_EXECUTORS = None

MAX_NUM_STATE_CHANGE = 40
MIN_NUM_STATE_CHANGE = 30

MAX_NUM_PARALLEL = None
MIN_NUM_PARALLEL = None


def GetExecutorId(local_id: int, local: bool):
    logger.debug(f'get executor id local {local}, local_id {local_id}')
    if local:
        return local_id

    ids = [i for i in range(NUM_EXECUTORS) if i != local_id]
    return random.choice(ids)


def RandomNumStateChange() -> int:
    return random.randrange(MIN_NUM_STATE_CHANGE, MAX_NUM_STATE_CHANGE+1)


def RandomNumPara() -> int:
    return random.randrange(MIN_NUM_PARALLEL, MAX_NUM_PARALLEL+1)


def ByteArraySvStr(ba: bytearray) -> str:
    ss = [f'8\'h{b:x}' for b in ba]
    sj = ','.join(ss)
    return '{'+sj+'}'


class Cacheline:
    def __init__(self) -> None:
        self.home: int = None
        self.addr: int = None
        self.value: bytearray = None

    def ValueSvStr(self) -> str:
        ss = [f'8\'h{b:x}' for b in self.value]
        sj = ','.join(ss)
        return '{'+sj+'}'


cacheline_pool: list[Cacheline] = []

SET = 4096
WAY = 4
# 不要超过组相联数量，因为本测试的目标是测试 cacheline 的状态转换，而不是测试替换能力
# 并且超过组相联约束会破坏状态转换
NUM_CL_IN_SET = WAY
SET_SHIFT = 6
WAY_SHIFT = 12+SET_SHIFT

for i in range(int(1024/NUM_CL_IN_SET)):
    for ci in range(NUM_CL_IN_SET):
        cl = Cacheline()
        cl.addr = 0x17000000000 + (i << SET_SHIFT) + (ci << WAY_SHIFT)
        cacheline_pool.append(cl)


def SampleCachlines(num: int) -> list[Cacheline]:
    assert (num <= len(cacheline_pool))
    return random.sample(cacheline_pool, num)


def RandomCacheValue(num: int = 64) -> bytes:
    rba = bytearray(num)
    for i in range(num):
        v = random.randrange(0, 256)
        rba[i] = v
    return bytes(rba)

# uvm
# request


class RequestAction(Action):
    def __init__(self, cl: Cacheline, local: bool = True, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl
        self.local = local
        self.executor_id = GetExecutorId(cl.home, local)

# read


class ReadOnce(RequestAction):
    def Body(self):
        assert (self.cl.value is not None)
        self.sv_src = f'exec.ReadOnce({self.addr, self.value})'

# class ReadOnceCleanInvalid(RequestAction):
#   def Body(self):
#     pass


class ReadClean(RequestAction):
    def Body(self):
        assert (self.cl.value is not None)
        self.sv_src = f'exec.ReadClean(64\'h{self.cl.addr:x}, {self.cl.ValueSvStr()});'


class ReadNotSharedDirty(RequestAction):
    def Body(self):
        assert (self.cl.value is not None)
        self.sv_src = f'exec.ReadNotSharedDirty(64\'h{self.cl.addr:x}, {self.cl.ValueSvStr()});'


class ReadShared(RequestAction):
    def Body(self):
        assert (self.cl.value is not None)
        self.sv_src = f'exec.ReadShared(64\'h{self.cl.addr:x}, {self.cl.ValueSvStr()});'


class ReadUnique(RequestAction):
    def Body(self):
        assert (self.cl.value is not None)
        self.sv_src = f'exec.ReadUnique(64\'h{self.cl.addr:x}, {self.cl.ValueSvStr()});'


class ReadPreferUnique(RequestAction):
    def Body(self):
        assert (self.cl.value is not None)
        self.sv_src = f'exec.ReadPreferUnique(64\'h{self.cl.addr:x}, {self.cl.ValueSvStr()});'

# dataless


class CleanUnique(RequestAction):
    def Body(self):
        self.sv_src = f'exec.CleanUnique(64\'h{self.cl.addr:x});'


class MakeUnique(RequestAction):
    def Body(self):
        self.cl.value = RandomCacheValue()
        self.sv_src = f'exec.MakeUnique(64\'h{self.cl.addr:x}, {self.cl.ValueSvStr()});'

# class Evict(RequestAction): in SafeEvict
#   def Body(self):
#     self.sv_src = f'exec.Evict(64\'h{self.cl.addr:x});'

# class StashOnceUnique(RequestAction):
#   def Body(self):
#     pass

# class StashOnceShared(RequestAction):
#   def Body(self):
#     pass

# cache maintenance


class CleanShared(RequestAction):
    def Body(self):
        self.sv_src = f'exec.CleanShared(64\'h{self.cl.addr:x});'

# class CleanSharedPersist(RequestAction):
#   def Body(self):
#     pass


class CleanInvalid(RequestAction):
    def Body(self):
        self.sv_src = f'exec.CleanInvalid(64\'h{self.cl.addr:x});'

# 丢弃 dirty 副本，暂时无法测试，因为丢弃以后，无法检查后续值是否正确
# 需要记住上次写回的值


class MakeInvalid(RequestAction):
    def Body(self):
        self.sv_src = f'exec.MakeInvalid(64\'h{self.cl.addr:x});'

# write
# class WriteUniqueFull(RequestAction):
#   def Body(self):
#     pass

# copyback
# class WriteBackFull(RequestAction): --> in SafeEvict
#   def Body(self):
#     self.sv_src = f'exec.WriteBackFull(64\'h{self.cl.addr:x});'


class WriteCleanFull(RequestAction):
    def Body(self):
        self.sv_src = f'exec.WriteCleanFull(64\'h{self.cl.addr:x});'

# class WriteEvictFull(RequestAction): 00> in SafeEvict
#   def Body(self):
#     self.sv_src = f'exec.WriteEvictFull(64\'h{self.cl.addr:x});'

# Evict, WriteEvictFull, WriteBackFull
# dirty 状态由于 PD 的存储，静态生成时不能预知，evict 时必须根据是否为 dirty
# 决定使用何种方式


class SafeEvict(RequestAction):
    def Body(self):
        self.sv_src = f'exec.SafeEvict(64\'h{self.cl.addr:x});'

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
        self.txn_value = RandomCacheValue(self.size)
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


class AtomicLoad(RequestAction):
    def Body(self):
        aso = AtomicLoadStoreOps(self.cl.value)
        aso.Randomize()
        self.sv_src = f'exec.AtomicLoad(64\'h{self.cl.addr:x}, {ByteArraySvStr(aso.init_value)}, {ByteArraySvStr(aso.txn_value)}, 8\'d{aso.offset}, 8\'d{aso.size}, {CdnChiAtomicLoadOpcode(aso.op)});'
        self.cl.value = aso.updated_cl_value


class AtomicStore(RequestAction):
    def Body(self):
        aso = AtomicLoadStoreOps(self.cl.value)
        aso.Randomize()
        self.sv_src = f'exec.AtomicStore(64\'h{self.cl.addr:x}, {ByteArraySvStr(aso.txn_value)}, 8\'d{aso.offset}, 8\'d{aso.size}, {CdnChiAtomicStoreOpcode(aso.op)});'
        self.cl.value = aso.updated_cl_value


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
        self.swap_value = RandomCacheValue(self.size)
        self.init_value = bytearray(self.init_cl_value[lo:hi])
        self.updated_cl_value[lo:hi] = self.swap_value


class AtomicSwap(RequestAction):
    def Body(self):
        aso = AtomicSwapOps(self.cl.value)
        aso.Randomize()
        self.sv_src = f'exec.AtomicSwap(64\'h{self.cl.addr:x}, {ByteArraySvStr(aso.init_value)}, {ByteArraySvStr(aso.swap_value)}, 8\'d{aso.offset}, 8\'d{aso.size});'
        self.cl.value = aso.updated_cl_value

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
        self.offset = random.randrange(0, 64)
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
        self.swap_value = RandomCacheValue(self.size)

        if self.match == 1:
            self.cmp_value = bytearray(self.init_value)
            self.updated_cl_value[lo:hi] = self.swap_value
        else:
            self.cmp_value = bytearray(self.init_value)
            self.cmp_value[0] = (self.cmp_value[0] + 1) & 0xFF


class AtomicCompare(RequestAction):
    def Body(self):
        aso = AtomicCompareOps(self.cl.value)
        aso.Randomize()
        self.sv_src = f'exec.AtomicCompare(64\'h{self.cl.addr:x}, {ByteArraySvStr(aso.init_value)}, {ByteArraySvStr(aso.cmp_value)}, {ByteArraySvStr(aso.swap_value)}, 8\'d{aso.offset}, 8\'d{aso.size});'
        self.cl.value = aso.updated_cl_value


class AtomicAction(RequestAction):
    def Activity(self):
        Select(AtomicLoad(self.cl, self.local),
               AtomicStore(self.cl, self.local),
               AtomicSwap(self.cl, self.local),
               AtomicCompare(self.cl, self.local))

# derived requests
# 修改本地分布，预期其处于 unique 态，如果不是则警告，并进入 UD 态


class Modify(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Body(self):
        self.executor_id = self.cl.home
        self.cl.value = RandomCacheValue()
        self.sv_src = f'exec.Modify(64\'h{self.cl.addr:x}, {self.cl.ValueSvStr()});'

# read unique and modify to be dirty


class WriteWithReadUnique(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(ReadUnique(self.cl))
        Do(Modify(self.cl))


class InitReadUnique(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl
        self.executor_id = GetExecutorId(cl.home, False)

    def Body(self):
        self.cl.value = RandomCacheValue()
        self.sv_src = f'exec.Modify(64\'h{self.cl.addr:x}, {self.cl.ValueSvStr()});'


class CheckSharedClean(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Body(self):
        self.executor_id = cl.home
        self.sv_src = f'exec.CheckShared(64\'h{self.cl.addr:x}, 0);'


class CheckSharedDirty(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Body(self):
        self.executor_id = cl.home
        self.sv_src = f'exec.CheckShared(64\'h{self.cl.addr:x}, 1);'
# snoop


class SnpAction(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl


class SnpOnce(SnpAction):
    def Activity(self):
        Do(ReadOnce(self.cl, False))

# class SnpStashUnique(SnpAction):
#   pass

# class SnpStashShared(SnpAction):
#   pass


class SnpClean(SnpAction):
    def Activity(self):
        Do(ReadClean(self.cl, False))


class SnpNotSharedDirty(SnpAction):
    def Activity(self):
        Do(ReadNotSharedDirty(self.cl, False))


class SnpShared(SnpAction):
    def Activity(self):
        Do(ReadShared(self.cl, False))


class SnpUnique(SnpAction):
    def Activity(self):
        # Do(ReadUnique(self.cl, False))
        Select(ReadUnique(self.cl, False),
               #  atomic 可能在 shared 状态发出，必须 safe evict
               AtomicAction(self.cl, False))

# class SnpPreferUnique(SnpAction):
#   def Activity(self):
#     Do(ReadPreferUnique(self.cl, False))

# class SnpUniqueStash(SnpAction):
#   pass


class SnpCleanShared(SnpAction):
    def Activity(self):
        Do(CleanShared(self.cl, False))


class SnpCleanInvalid(SnpAction):
    def Activity(self):
        Do(CleanInvalid(self.cl, False))

# class SnpMakeInvalid(SnpAction):
#   pass

# class SnpMakeInvalidStash(SnpAction):
#   pass

# class SnpQuery(SnpAction):
#   pass

# class SnpDVMOp(SnpAction):
#   pass


class State(Enum):
    Invalid = 1
    UniqueClean = 2
    UniqueCleanEmpty = 3
    UniqueDirty = 4
    UniqueDirtyPartial = 5
    SharedClean = 6
    SharedDirty = 7
    # 处理不确定情况时的综合状态
    # SharedClean, UniqueClean
    Clean = 8
    # SharedClean, SharedDirty, UniqueClean, UniqueDirty
    Valid = 9
    # SharedClean, UniqueClean, UniqueDirty
    NotSharedDirty = 10
    # UniqueDirty, UniqueClean
    Unique = 11
    # SharedClean, SharedDirty
    Shared = 12

# ReadClean: SharedClean, UniqueClean
# ReadShared: SharedClean, SharedDirty, UniqueClean, UniqueDirty
# ReadNotSharedDirty: SharedClean, UniqueClean, UniqueDirty


@StateTransition(State.Invalid, State.Clean)
class InvalidToClean(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(ReadClean(self.cl))


@StateTransition(State.Invalid, State.Valid)
class InvalidToValid(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(ReadShared(self.cl))


@StateTransition(State.Invalid, State.NotSharedDirty)
class InvalidToNotSharedDirty(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(ReadNotSharedDirty(self.cl))


@StateTransition(State.Invalid, State.UniqueDirty)
class InvalidToUniqueDirty(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(MakeUnique(self.cl))


@StateTransition(State.Invalid, State.Unique)
class InvalidToUnique(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(ReadUnique(self.cl))


@StateTransition(State.UniqueClean, State.Invalid)
class UniqueCleanToInvalid(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(SafeEvict(self.cl),
               SnpUnique(self.cl),
               SnpCleanInvalid(self.cl))


@StateTransition(State.UniqueClean, State.UniqueDirty)
class UniqueCleanToUniqueDirty(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Modify(self.cl))


@StateTransition(State.UniqueClean, State.SharedClean)
class UniqueCleanToSharedClean(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(SnpClean(self.cl),
               SnpShared(self.cl),
               SnpNotSharedDirty(self.cl))


@StateTransition(State.UniqueDirty, State.Invalid)
class UniqueDirtyToInvalid(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        # UniqueToInvalid 不允许使用 Atomic 操作
        Select(SafeEvict(self.cl),
               SnpUnique(self.cl),
               SnpCleanInvalid(self.cl))


@StateTransition(State.UniqueDirty, State.UniqueClean)
class UniqueDirtyToUniqueClean(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(WriteCleanFull(self.cl),
               SnpCleanShared(self.cl))


@StateTransition(State.UniqueDirty, State.Shared)
class UniqueDirtyToShared(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(SnpClean(self.cl),
               SnpShared(self.cl),
               SnpNotSharedDirty(self.cl))

# 来自其他 rnf 的读请求
# class SharedCleanToSharedClean(Action):
#   def __init__(self, cl: Cacheline, name: str = None) -> None:
#     super().__init__(name)
#     self.cl = cl


@StateTransition(State.SharedClean, State.Invalid)
class SharedCleanToInvalid(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(SafeEvict(self.cl),
               CleanInvalid(self.cl),
               SnpUnique(self.cl),
               SnpCleanInvalid(self.cl))


@StateTransition(State.SharedClean, State.UniqueClean)
class SharedCleanToUniqueClean(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(CleanUnique(self.cl))


@StateTransition(State.SharedClean, State.UniqueDirty)
class SharedCleanToUniqueDirty(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(MakeUnique(self.cl))


@StateTransition(State.SharedClean, State.Unique)
class SharedCleanToUnique(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(ReadUnique(self.cl))

# 貌似没有办法保证到达 SharedDirty，除非 executor 中提供一个函数
# 必须要求到达 SharedDirty，否则报错或是警告，例如从 UniqueDirty
# 到 SharedDirty


@StateTransition(State.SharedDirty, State.Invalid)
class SharedDirtyToInvalid(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(SafeEvict(self.cl),
               CleanInvalid(self.cl),
               SnpUnique(self.cl),
               SnpCleanInvalid(self.cl))


@StateTransition(State.SharedDirty, State.UniqueDirty)
class SharedDirtyToUniqueDirty(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(CleanUnique(self.cl),
               MakeUnique(self.cl))

# possible transition


@StateTransition(State.SharedDirty, State.SharedClean)
class SharedDirtyToSharedClean(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(SnpClean(self.cl),
               SnpShared(self.cl),
               SnpNotSharedDirty(self.cl))


@StateTransition(State.Clean, State.Invalid)
class CleanToInvalid(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(SafeEvict(self.cl),
               CleanInvalid(self.cl),
               SnpUnique(self.cl),
               SnpCleanInvalid(self.cl))


@StateTransition(State.Clean, State.Unique)
class CleanToUnique(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(ReadUnique(self.cl),
               CleanUnique(self.cl))


@StateTransition(State.Clean, State.UniqueDirty)
class CleanToUniqueDirty(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(MakeUnique(self.cl))


@StateTransition(State.Clean, State.SharedClean)
class CleanToSharedClean(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(SnpClean(self.cl),
               SnpShared(self.cl),
               SnpNotSharedDirty(self.cl))


@StateTransition(State.Valid, State.Invalid)
class ValidToUnique(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(SafeEvict(self.cl),
               CleanInvalid(self.cl),
               SnpUnique(self.cl),
               SnpCleanInvalid(self.cl))


@StateTransition(State.Valid, State.Unique)
class ValidToUnique(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(ReadUnique(self.cl),
               CleanUnique(self.cl))


@StateTransition(State.Valid, State.UniqueDirty)
class ValidToUniqueDirty(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(MakeUnique(self.cl))


@StateTransition(State.Valid, State.Shared)
class ValidToShared(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        # TOFIX
        # 如何判断不做任何操作？
        # 如果是 unique 需要 snoop 才能进入 shared
        Select(SnpClean(self.cl),
               SnpShared(self.cl),
               SnpNotSharedDirty(self.cl))


@StateTransition(State.NotSharedDirty, State.Invalid)
class NotSharedDirtyToInvalid(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(SafeEvict(self.cl),
               CleanInvalid(self.cl),
               SnpUnique(self.cl),
               SnpCleanInvalid(self.cl))


@StateTransition(State.NotSharedDirty, State.Unique)
class NotSharedDirtyToUnique(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(ReadUnique(self.cl),
               CleanUnique(self.cl))


@StateTransition(State.NotSharedDirty, State.UniqueDirty)
class NotSharedDirtyToUniqueDirty(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(MakeUnique(self.cl))


@StateTransition(State.NotSharedDirty, State.SharedClean)
class NotSharedDirtyToSharedClean(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(SnpClean(self.cl),
               SnpShared(self.cl),
               SnpNotSharedDirty(self.cl))


@StateTransition(State.Unique, State.UniqueDirty)
class UniqueToUniqueDirty(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(Modify(self.cl))


@StateTransition(State.Unique, State.UniqueClean)
class UniqueToUniqueClean(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(WriteCleanFull(self.cl))


@StateTransition(State.Shared, State.SharedClean)
class SharedToSharedClean(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(CheckSharedClean(self.cl))


@StateTransition(State.Shared, State.SharedDirty)
class SharedToSharedClean(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(CheckSharedDirty(self.cl))


class StressCacheline(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        num_state_change = RandomNumStateChange()
        acts = StateInfer(SharedCleanToUniqueClean,
                          num_state_change, State.Invalid)
        for act in acts:
            Do(act(self.cl))


class StressMultiCacheline(Action):
    def Activity(self):
        num_para = RandomNumPara()
        cls = SampleCachlines(num_para)
        with Parallel():
            for i in range(num_para):
                with Sequence():
                    cl = cls[i]
                    cl.value = None
                    cl.home = random.randrange(0, NUM_EXECUTORS)
                    # init with a writting from bus
                    # 1. to invalid state
                    # 2. get init value
                    Do(InitReadUnique(cl))
                    logger.debug(f'home {cl.home}')
                    Do(StressCacheline(cl))


class TargetSync(Action):
    def Body(self):
        self.sv_src = '// just sync'


class ChiStateTrnsTest(Action):
    def __init__(self, rpt_times: int) -> None:
        super().__init__(None)
        self.rpt_times = rpt_times

    def Activity(self):
        for i in range(self.rpt_times):
            print(f'iter: {i}')
            Do(TargetSync())
            Do(StressMultiCacheline())


def Main():
    global NUM_EXECUTORS
    global MAX_NUM_PARALLEL
    global MIN_NUM_PARALLEL

    # logging.basicConfig(filename='build/myapp.log', filemode='w', level=logging.INFO)
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    purslane.dsl.PrepareArgParser(parser)

    # parser.add_argument('--num_parallel', type=int, default=None)
    # parser.add_argument('--max_num_state_change', type=int, default=30)
    parser.add_argument('--num_repeat_times', type=int, default=2)

    args = parser.parse_args()

    if args.num_executors < 2:
        raise ('need more than one executor')

    num_repeat_times = args.num_repeat_times

    NUM_EXECUTORS = args.num_executors
    MAX_NUM_PARALLEL = NUM_EXECUTORS * 64
    MIN_NUM_PARALLEL = NUM_EXECUTORS * 16

    # MIN_NUM_PARALLEL = 4
    # MAX_NUM_PARALLEL = 8

    # with (TypeOverride(mosei.ReadShared, ReadUniqueUVM),
    #       TypeOverride(mosei.ReadUnique, ReadUniqueUVM),
    #       TypeOverride(mosei.Write, WriteUVM),
    #       TypeOverride(mosei.Invalidate, InvalidateUVM)):
    Run(ChiStateTrnsTest(num_repeat_times), args)


if __name__ == '__main__':
    Main()
