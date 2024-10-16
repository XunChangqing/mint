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
        self.value: bytearray = None

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

# @StateTransition(State.Init, State.Modified)
# class InitToModified(Action):
#     def __init__(self, cl: Cacheline, name: str = None) -> None:
#         super().__init__(name)
#         self.cl = cl

#     def Activity(self):
#         Do(LocalWrite(self.cl))


@StateTransition(State.Invalid, State.Exclusive)
class InvalidToExclusive(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(LocalRead(self.cl))


@StateTransition(State.Exclusive, State.Exclusive)
class ExclusiveToExclusive(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(LocalRead(self.cl))


@StateTransition(State.Exclusive, State.Modified)
class ExclusiveToModified(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(LocalWrite(self.cl))


@StateTransition(State.Invalid, State.Modified)
class InvalidToModified(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(LocalWrite(self.cl))


@StateTransition(State.Owned, State.Modified)
class OwnedToModified(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(LocalWrite(self.cl))


@StateTransition(State.Shared, State.Modified)
class OwnedToModified(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(LocalWrite(self.cl))


@StateTransition(State.Modified, State.Modified)
class ModifiedToModifiedRead(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(LocalRead(self.cl))


@StateTransition(State.Modified, State.Modified)
class ModifiedToModifiedWrite(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(LocalWrite(self.cl))

@StateTransition(State.Modified, State.Owned)
class ModifiedToOwned(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(SnoopRead(self.cl))

@StateTransition(State.Modified, State.Exclusive)
class ModifiedToExclusive(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(
            LocalClean(self.cl),
            CleanDomain(self.cl)
        )


@StateTransition(State.Owned, State.Owned)
class OwnedToOwnedRead(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(LocalRead(self.cl))


@StateTransition(State.Owned, State.Owned)
class OwnedToOwnedSnoopRead(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(SnoopRead(self.cl))


@StateTransition(State.Invalid, State.Shared)
class InvalidToSharedShared(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(SnoopRead(self.cl))
        Do(LocalRead(self.cl))


@StateTransition(State.Invalid, State.Shared)
class InvalidToSharedModified(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(SnoopWrite(self.cl))
        Do(LocalRead(self.cl))


@StateTransition(State.Exclusive, State.Shared)
class ExclusiveToSharedModified(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(SnoopRead(self.cl))


@StateTransition(State.Shared, State.Shared)
class SharedToSharedRead(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(LocalRead(self.cl))


@StateTransition(State.Shared, State.Shared)
class SharedToSharedSnoopRead(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(SnoopRead(self.cl))


@StateTransition(State.Invalid, State.Shared)
class InvalidToSharedModified(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(SnoopWrite(self.cl))
        Do(LocalRead(self.cl))


@StateTransition(State.Exclusive, State.Invalid)
class ExclusiveToInvalid(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(SnoopWrite(self.cl))


@StateTransition(State.Modified, State.Invalid)
class ModifiedToInvalid(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(SnoopWrite(self.cl))


@StateTransition(State.Owned, State.Invalid)
class OwnedToInvalid(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(SnoopWrite(self.cl))


@StateTransition(State.Shared, State.Invalid)
class SharedToInvalid(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Do(SnoopWrite(self.cl))


@StateTransition(State.Invalid, State.Invalid)
class InvalidToInvalidWBINVD(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(
            LocalClean(self.cl),
            LocalCleanInvalidate(self.cl),
        )


@StateTransition(State.Exclusive, State.Invalid)
class ExclusiveToInvalidWBINVD(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(
            LocalCleanInvalidate(self.cl),
            CleanInvalidateDomain(self.cl),
            )


@StateTransition(State.Modified, State.Invalid)
class ModifiedToInvalidWBINVD(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(
            LocalCleanInvalidate(self.cl),
            CleanInvalidateDomain(self.cl)
        )


@StateTransition(State.Owned, State.Invalid)
class OwnedToInvalidWBINVD(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(
            LocalCleanInvalidate(self.cl),
            CleanInvalidateDomain(self.cl),
        )


@StateTransition(State.Shared, State.Invalid)
class SharedToInvalidWBINVD(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        Select(
            LocalCleanInvalidate(self.cl),
            CleanInvalidateDomain(self.cl)
        )


class StressCacheline(Action):
    def __init__(self, cl: Cacheline, name: str = None) -> None:
        super().__init__(name)
        self.cl = cl

    def Activity(self):
        # init as modified in order to check
        init_act = Init(self.cl)
        init_act.executor_id = self.cl.home
        Do(init_act)

        dest_state = random.choice([State.Invalid,
                                    State.Shared,
                                    State.Exclusive,
                                    State.Modified,
                                    State.Owned])
        num_state_change = RandomNumStateChange()
        # num_state_change = 2
        acts = StateInfer(dest_state, num_state_change, State.Modified)
        for act in acts:
            Do(act(self.cl))


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
            logger.info(f'iter: {i}')
            Do(TargetSync())
            Do(StressMultiCacheline())
