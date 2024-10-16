# author: zuoqian
# Copyright 2024. All rights reserved.


from enum import Enum
import random
import argparse
import logging
import typing
import purslane.dsl
import purslane.state
from purslane.dsl import Do, Action, Sequence, Parallel, Select, Run, TypeOverride
from purslane.state import StateTransition, StateInfer

logger = logging.getLogger(__name__)


BodyNotImplemented = NotImplementedError('action body')

NUM_EXECUTORS = None

MAX_NUM_STATE_CHANGE = 40
MIN_NUM_STATE_CHANGE = 30

MAX_NUM_PARALLEL = None
MIN_NUM_PARALLEL = None


def RandomRemoteExecutorId(local_id: int):
    ids = [i for i in range(NUM_EXECUTORS) if i != local_id]
    return random.choice(ids)


def RandomNumStateChange() -> int:
    return random.randrange(MIN_NUM_STATE_CHANGE, MAX_NUM_STATE_CHANGE+1)


def RandomNumPara() -> int:
    return random.randrange(MIN_NUM_PARALLEL, MAX_NUM_PARALLEL+1)


class Cacheline:
    def __init__(self) -> None:
        self.home: int = None
        self.addr: int = None
        self.rec_limit = RandomNumStateChange()
        self.value: bytearray = None

    def RecLimt(self) -> bool:
        self.rec_limit-=1
        logger.debug(f'rec limt {self.rec_limit}')
        return self.rec_limit <= 0

    def ValueSvStr(self) -> str:
        ss = [f'8\'h{b:x}' for b in self.value]
        sj = ','.join(ss)
        return '{'+sj+'}'


class CachelinePool:
    def __init__(self) -> None:
        pass

    def Alloc(self) -> Cacheline:
        raise NotImplementedError("cacheline pool Alloc")

    def Free(self, cl: Cacheline) -> None:
        raise NotImplementedError("cacheline pool Free")


cacheline_pool: CachelinePool = None


class State(Enum):
    Invalid = 1
    Shared = 2
    Exclusive = 3
    Modified = 4
    Owned = 5

# 按照通用的 MOESI 模型控制状态转移，实际上由于 cache 实现时微架构细节，不能保证状态
# 会按照预取到达

# action interface


class Read(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        raise BodyNotImplemented

    def Body(self):
        raise BodyNotImplemented


class Write(Action):
    # size 2^size bytes
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        raise BodyNotImplemented

    def Body(self):
        raise BodyNotImplemented


class Clean(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        raise BodyNotImplemented

    def Body(self):
        raise BodyNotImplemented


class CleanInvalidate(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        raise BodyNotImplemented

    def Body(self):
        raise BodyNotImplemented


class CleanDomain(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        raise BodyNotImplemented

    def Body(self):
        raise BodyNotImplemented


class CleanInvalidateDomain(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        raise BodyNotImplemented

    def Body(self):
        raise BodyNotImplemented

class WriteNoAlloc(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        raise BodyNotImplemented

    def Body(self):
        raise BodyNotImplemented


class Init(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        raise BodyNotImplemented

    def Body(self):
        raise BodyNotImplemented


# basic actions


class LocalRead(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl
        self.executor_id = cl.home

    def Activity(self):
        Do(Read(self.cl, self.name))


class LocalWrite(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl
        self.executor_id = cl.home

    def Activity(self):
        Do(Write(self.cl, self.name))


class SnoopRead(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl
        self.executor_id = RandomRemoteExecutorId(self.cl.home)

    def Activity(self):
        Do(Read(self.cl, self.name))


class SnoopWrite(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl
        self.executor_id = RandomRemoteExecutorId(self.cl.home)

    def Activity(self):
        Select(
            Write(self.cl, self.name),
            WriteNoAlloc(self.cl, self.name),
        )


class LocalClean(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl
        self.executor_id = cl.home

    def Activity(self):
        Do(Clean(self.cl, self.name))


class LocalCleanInvalidate(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl
        self.executor_id = cl.home

    def Activity(self):
        Do(CleanInvalidate(self.cl, self.name))


# state transitions

class ModifiedFromInit(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        logger.debug(f'{self.GetClassName()}')
        Do(Init(self.cl))


class ExclusiveFromInvalid(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Invalid(self.cl))
        Do(LocalRead(self.cl))
        logger.debug(f'{self.GetClassName()}')


class ExclusiveFromExclusive(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Exclusive(self.cl))
        Do(LocalRead(self.cl))
        logger.debug(f'{self.GetClassName()}')


class ModifiedFromExclusive(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Exclusive(self.cl))
        Do(LocalWrite(self.cl))
        logger.debug(f'{self.GetClassName()}')


class ModifiedFromInvalid(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Invalid(self.cl))
        Do(LocalWrite(self.cl))
        logger.debug(f'{self.GetClassName()}')


class ModifiedFromOwned(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Owned(self.cl))
        Do(LocalWrite(self.cl))
        logger.debug(f'{self.GetClassName()}')


class ModifiedFromOwned(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Owned(self.cl))
        Do(LocalWrite(self.cl))
        logger.debug(f'{self.GetClassName()}')


class ModifiedFromModifiedRead(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Modified(self.cl))
        Do(LocalRead(self.cl))
        logger.debug(f'{self.GetClassName()}')


class ModifiedFromModifiedWrite(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Modified(self.cl))
        Do(LocalWrite(self.cl))
        logger.debug(f'{self.GetClassName()}')

class OwnedFromModifed(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Modified(self.cl))
        Do(SnoopRead(self.cl))
        logger.debug(f'{self.GetClassName()}')


class ExclusiveFromModifed(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Modified(self.cl))
        Select(
            LocalClean(self.cl),
            CleanDomain(self.cl)
        )
        logger.debug(f'{self.GetClassName()}')


class OwnedFromOwnedRead(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Owned(self.cl))
        Do(LocalRead(self.cl))
        logger.debug(f'{self.GetClassName()}')


class OwnedFromOwnedSnoopRead(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Owned(self.cl))
        Do(SnoopRead(self.cl))
        logger.debug(f'{self.GetClassName()}')


class SharedFromInvalidShared(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Invalid(self.cl))
        Do(SnoopRead(self.cl))
        Do(LocalRead(self.cl))
        logger.debug(f'{self.GetClassName()}')


class SharedFromInvalidModified(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Invalid(self.cl))
        Do(SnoopWrite(self.cl))
        Do(LocalRead(self.cl))
        logger.debug(f'{self.GetClassName()}')


class SharedFromExclusiveModified(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Exclusive(self.cl))
        Do(SnoopRead(self.cl))
        logger.debug(f'{self.GetClassName()}')


class SharedFromSharedRead(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Shared(self.cl))
        Do(LocalRead(self.cl))
        logger.debug(f'{self.GetClassName()}')


class SharedFromSharedSnoopRead(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Shared(self.cl))
        Do(SnoopRead(self.cl))
        logger.debug(f'{self.GetClassName()}')


class SharedFromInvalidModified(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Invalid(self.cl))
        Do(SnoopWrite(self.cl))
        Do(LocalRead(self.cl))
        logger.debug(f'{self.GetClassName()}')


class InvalidFromExclusive(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Exclusive(self.cl))
        Do(SnoopWrite(self.cl))
        logger.debug(f'{self.GetClassName()}')


class InvalidFromModified(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Modified(self.cl))
        Do(SnoopWrite(self.cl))
        logger.debug(f'{self.GetClassName()}')


class InvalidFromOwned(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Owned(self.cl))
        Do(SnoopWrite(self.cl))
        logger.debug(f'{self.GetClassName()}')


class InvalidFromShared(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Shared(self.cl))
        Do(SnoopWrite(self.cl))
        logger.debug(f'{self.GetClassName()}')


class InvalidFromInvalidWBINVD(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Invalid(self.cl))
        Select(
            LocalClean(self.cl),
            LocalCleanInvalidate(self.cl),
        )
        logger.debug(f'{self.GetClassName()}')


class InvalidFromExclusiveWBINVD(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Exclusive(self.cl))
        Select(
            LocalCleanInvalidate(self.cl),
            CleanInvalidateDomain(self.cl),
        )
        logger.debug(f'{self.GetClassName()}')


class InvalidFromModifiedWBINVD(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Modified(self.cl))
        Select(
            LocalCleanInvalidate(self.cl),
            CleanInvalidateDomain(self.cl)
        )
        logger.debug(f'{self.GetClassName()}')


class InvalidFromOwnedWBINVD(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Owned(self.cl))
        Select(
            LocalCleanInvalidate(self.cl),
            CleanInvalidateDomain(self.cl),
        )
        logger.debug(f'{self.GetClassName()}')


class InvalidFromSharedWBINVD(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(Shared(self.cl))
        Select(
            LocalCleanInvalidate(self.cl),
            CleanInvalidateDomain(self.cl)
        )
        logger.debug(f'{self.GetClassName()}')

# states
class Modified(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl
    
    def Activity(self):
        if self.cl.RecLimt():
            Do(ModifiedFromInit(self.cl))
        else:
            Select(
                ModifiedFromOwned(self.cl),
                ModifiedFromExclusive(self.cl),
                ModifiedFromInvalid(self.cl),
                ModifiedFromModifiedRead(self.cl),
                ModifiedFromModifiedWrite(self.cl),
            )

class Owned(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl
    
    def Activity(self):
        if self.cl.RecLimt():
            Do(OwnedFromModifed(self.cl))
        else:
            Select(
                OwnedFromModifed(self.cl),
                OwnedFromOwnedRead(self.cl),
                OwnedFromOwnedSnoopRead(self.cl),
            )

class Exclusive(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl
    
    def Activity(self):
        if self.cl.RecLimt():
            Do(ExclusiveFromModifed(self.cl))
        else:
            Select(
                ExclusiveFromExclusive(self.cl),
                ExclusiveFromInvalid(self.cl),
                ExclusiveFromModifed(self.cl),
            )

class Shared(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl
    
    def Activity(self):
        if self.cl.RecLimt():
            Do(SharedFromExclusiveModified(self.cl))
        else:
            Select(
                SharedFromExclusiveModified(self.cl),
                SharedFromInvalidModified(self.cl),
                SharedFromInvalidShared(self.cl),
                SharedFromSharedRead(self.cl),
                SharedFromSharedSnoopRead(self.cl),
            )

class Invalid(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl
    
    def Activity(self):
        if self.cl.RecLimt():
            Do(InvalidFromModified(self.cl))
        else:
            Select(
                InvalidFromExclusive(self.cl),
                InvalidFromExclusiveWBINVD(self.cl),
                InvalidFromInvalidWBINVD(self.cl),
                InvalidFromModified(self.cl),
                InvalidFromModifiedWBINVD(self.cl),
                InvalidFromOwned(self.cl),
                InvalidFromOwnedWBINVD(self.cl),
                InvalidFromShared(self.cl),
                InvalidFromSharedWBINVD(self.cl),
            )


class StressCacheline(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(
            Modified(self.cl),
            Owned(self.cl),
            Exclusive(self.cl),
            Shared(self.cl),
            Invalid(self.cl)
        )

class StressMultiCacheline(Action):
    def Activity(self):
        num_para = RandomNumPara()

        cls = []
        for i in range(num_para):
            cls.append(cacheline_pool.Alloc())

        with Parallel():
            for i in range(num_para):
                with Sequence():
                    cl = cls[i]
                    cl.value = None
                    cl.home = random.randrange(0, NUM_EXECUTORS)
                    Do(StressCacheline(cl))

        for cl in cls:
            cacheline_pool.Free(cl)


class TargetSync(Action):
    def Body(self):
        self.sv_src = '// just sync'
        self.c_src = '// just sync'


class MoesiTest(Action):
    def __init__(self, rpt_times: int) -> None:
        super().__init__(None)
        self.rpt_times = rpt_times

    def Activity(self):
        for i in range(self.rpt_times):
            logger.debug(f'iter: {i}')
            Do(TargetSync())
            Do(StressMultiCacheline())
