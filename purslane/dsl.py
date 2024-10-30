"""
author: zuoqian
Copyright 2024. All rights reserved.
"""

import random
import logging
import argparse
import typing
import sys
from pathlib import Path
from purslane import dag
logger = logging.getLogger(__name__)


class NameResolver:
    def __init__(self):
        self._name_dict = {}

    def Resolve(self, name: str) -> str:
        if name in self._name_dict:
            sn = self._name_dict[name]
            self._name_dict[name] += 1
            return f'{name}_{sn}'
        else:
            self._name_dict[name] = 1
            return f'{name}_0'


class Context:
    def __init__(self):
        self.name_resolver = NameResolver()
        self.graph = dag.Graph()
        self.scopes = []
        self.pred = None
        self.parent_executor_id = None
        self.num_executors = 0

    def PushScope(self, scope):
        # logger.debug(f'PushScope {scope.name}')
        if len(self.scopes) > 0:
            self.scopes[-1].SubScopeEnter(scope)
        self.scopes.append(scope)

    def PopScope(self, scope):
        # logger.debug(f'PopScope {scope.name}')
        assert (len(self.scopes) > 0)
        back = self.scopes.pop()
        assert (back == scope)

        if len(self.scopes) > 0:
            self.scopes[-1].SubScopeExit(scope)


global_ctx = Context()


class Action:
    @classmethod
    def GetClassName(cls):
        return cls.__name__

    def __init__(self, name: str = None) -> None:
        if name is None:
            name = self.GetClassName()

        self.name = global_ctx.name_resolver.Resolve(name)
        self.sv_src: str = None
        self.c_src: str = None
        self.c_headers = None
        self.c_header = None
        self.c_decl = None
        self.executor_id = None

        self.scope = None
        self.deps: typing.List[Action] = []

    # def Activity(self):
    #   with Parallel():
        # 内部每个 action 都是 parallel 的

    # def Body(self):
    #   pass

# structural


class Sequence:
    def __init__(self) -> None:
        self.name = global_ctx.name_resolver.Resolve('seq')
        self.init_node = dag.Node(f'{self.name}_init')
        self.final_node = dag.Node(f'{self.name}_final')
        self.cur_pred = self.init_node
        self.sub_scopes = []

    def __enter__(self):
        global_ctx.graph.AddNode(self.init_node)
        global_ctx.PushScope(self)

    def __exit__(self, exc_type, exc_value, traceback):
        cur_pred = self.init_node
        for ss in self.sub_scopes:
            ss.init_node.AddPredecessor(cur_pred)
            cur_pred = ss.final_node
        self.final_node.AddPredecessor(cur_pred)

        global_ctx.graph.AddNode(self.final_node)
        global_ctx.PopScope(self)

    def SubScopeEnter(self, ss):
        self.sub_scopes.append(ss)
        # ss.init_node.AddPredecessor(self.cur_pred)

    def SubScopeExit(self, ss):
        pass
        # self.cur_pred = ss.final_node

# structural


class Parallel:
    def __init__(self) -> None:
        self.name = global_ctx.name_resolver.Resolve('para')
        self.init_node = dag.Node(f'{self.name}_init')
        self.final_node = dag.Node(f'{self.name}_final')
        # self._sub_scope_inits = []
        # self._sub_scope_finals = []
        self.sub_scopes = []

    def __enter__(self):
        global_ctx.graph.AddNode(self.init_node)
        global_ctx.PushScope(self)

    def __exit__(self, exc_type, exc_value, traceback):
        # 检查不同 sub scope 之间确实没有依赖
        # check if there is any dependency between different sub scopes
        # a final node that can reach any other init nodes indicates a dependency across sub-scopes.

        graph = dag.Graph()
        scopes = self.sub_scopes[:]

        while len(scopes) > 0:
            ss = scopes.pop()
            if ss.init_node is ss.final_node:
                graph.AddNode(ss.init_node)
            else:
                graph.AddNode(ss.init_node)
                graph.AddNode(ss.final_node)
            scopes.extend(ss.sub_scopes[:])
        
        graph.AssignSN()
        graph.UpdateAllPredecessors()

        for i, ss in enumerate(self.sub_scopes):
            cur_final = ss.final_node
            for j, ss2 in enumerate(self.sub_scopes):
                if i != j and ss2.init_node.sn in cur_final.all_predecessors:
                    logger.critical(f'dependence across sub-scopes of a parallel {ss.final_node.name} {ss2.init_node.name}')
                    raise 'dependence across sub-scopes of a parallel'

        if len(self.sub_scopes) > 0:
            for ss in self.sub_scopes:
                ss.init_node.AddPredecessor(self.init_node)
                self.final_node.AddPredecessor(ss.final_node)
        else:
            self.final_node.AddPredecessor(self.init_node)

        global_ctx.graph.AddNode(self.final_node)
        global_ctx.PopScope(self)

    def SubScopeEnter(self, ss):
        self.sub_scopes.append(ss)
        # self._sub_scope_inits.append(ss.init_node)

    def SubScopeExit(self, ss):
        pass
        # self._sub_scope_finals.append(ss.final_node)

# structrual


class Schedule:
    def __init__(self) -> None:
        self.name = global_ctx.name_resolver.Resolve('sched')
        self.init_node = dag.Node(f'{self.name}_init')
        self.final_node = dag.Node(f'{self.name}_final')
        self.sub_scopes = []

    def __enter__(self):
        global_ctx.graph.AddNode(self.init_node)
        global_ctx.PushScope(self)

    def __exit__(self, exc_type, exc_value, traceback):
        if len(self.sub_scopes) > 0:
            for ss in self.sub_scopes:
                ss.init_node.AddPredecessor(self.init_node)
                self.final_node.AddPredecessor(ss.final_node)
        else:
            self.final_node.AddPredecessor(self.init_node)

        global_ctx.graph.AddNode(self.final_node)
        global_ctx.PopScope(self)

    def SubScopeEnter(self, ss):
        self.sub_scopes.append(ss)
        # ss.init_node.AddPredecessor(self.init_node)

    def SubScopeExit(self, ss):
        pass
        # self._sub_scope_finals.append(ss.final_node)


class CompoundActionScope:
    def __init__(self, act: Action) -> None:
        self.name = act.name
        self.act = act
        act.scope = self
        self.init_node = dag.Node(f'{self.name}_init')
        self.final_node = dag.Node(f'{self.name}_final')
        self.cur_parent_executor_id = False
        self.sub_scopes = []
        # self.cur_pred = self.init_node

    def __enter__(self):
        global_ctx.graph.AddNode(self.init_node)
        global_ctx.PushScope(self)

        if global_ctx.parent_executor_id is None:
            if self.act.executor_id is not None:
                global_ctx.parent_executor_id = self.act.executor_id
                self.cur_parent_executor_id = True
            else:
                pass
        else:
            if self.act.executor_id is None:
                self.act.executor_id = global_ctx.parent_executor_id
            elif global_ctx.parent_executor_id != self.act.executor_id:
                raise ('the executor id of a child must follow its parent')

    def __exit__(self, exc_type, exc_value, traceback):
        global_ctx.graph.AddNode(self.final_node)

        cur_pred = self.init_node
        for ss in self.sub_scopes:
            ss.init_node.AddPredecessor(cur_pred)
            cur_pred = ss.final_node
        self.final_node.AddPredecessor(cur_pred)

        global_ctx.PopScope(self)

        if self.cur_parent_executor_id:
            global_ctx.parent_executor_id = None

    def SubScopeEnter(self, ss):
        self.sub_scopes.append(ss)
        # ss.init_node.AddPredecessor(self.cur_pred)

    def SubScopeExit(self, ss):
        pass
        # self.cur_pred = ss.final_node


class AtomicActionScope:
    def __init__(self, act: Action):
        self.name = act.name
        self.act = act
        act.scope = self
        self.target_node = dag.Node(f'{self.name}')
        self.target_node.is_target = True
        self.init_node = self.target_node
        self.final_node = self.target_node
        self.sub_scopes = []

    def __enter__(self) -> dag.Node:
        global_ctx.PushScope(self)
        global_ctx.graph.AddNode(self.target_node)

        if global_ctx.parent_executor_id is not None:
            if self.act.executor_id is not None:
                if global_ctx.parent_executor_id != self.act.executor_id:
                    raise ('the executor id of a child must follow its parent')
                else:
                    pass
            else:
                self.act.executor_id = global_ctx.parent_executor_id

        return self.target_node

    def __exit__(self, exc_type, exc_value, traceback):
        global_ctx.PopScope(self)

# behaviour


def Select(*actions):
    br_idx = random.randrange(0, len(actions))
    br = actions[br_idx]
    Do(br)

# type override for actions only


class TypeOverride:
    def __init__(self, original_type: type[Action], override_type: type[Action]) -> None:
        self.mod = sys.modules[original_type.__module__]
        self.original_type = original_type
        self.override_type = override_type

    def __enter__(self) -> None:
        setattr(self.mod, self.original_type.__name__, self.override_type)

    def __exit__(self, exc_type, exc_value, traceback):
        setattr(self.mod, self.original_type.__name__, self.original_type)


def PrepareArgParser(parser: argparse.ArgumentParser) -> None:
    # -S, --seed 设置随机种子
    # -F, --flist 源文件列表
    # --root 根组件名
    # --entry 入口action名
    # --num_executors 指定 executors 数量，soc 中一般是指处理核数量，uvm 中一般指某种 agent 数量，例如 chi rnf

    # --uvm_output 指定 uvm 输出文件
    # --uvm_pkg_name 指定输出 uvm 源码的 package 名字，不指定则生成代码没有 package
    # --uvm_executor_name 指定输出 uvm 源码中使用 executor 的类型名

    # --soc_output 指定 c 语言输出文件
    # --soc_cooperative 指定 c 语言输出线程框架为 cooperative 形式
    # --soc_cooperative_hosted 指定 cooperative 多线程时是否运行在操作系统上，编译时必须增加 -D_GNU_SOURCE
    # --soc_preemptive 指定 c 语言输出为抢占式多线程，基于 pthread，编译时必须增加 -D_GNU_SOURCE

    # parser = argparse.ArgumentParser()
    # parser.add_argument("testcase", metavar='testcase',
    #                     help="which testcase to build")
    parser.add_argument('-S', '--seed', help='random seed, default is random')
    parser.add_argument('--graph_output', default='graph.json',
                        help='graph output file name')
    parser.add_argument('--num_executors', default=2,
                        type=int, help='number of executors')
    parser.add_argument('--uvm_output', default=None, help='uvm output')
    parser.add_argument('--uvm_pkg_name', default=None,
                        help='uvm package name')
    parser.add_argument('--uvm_executor_name',
                        default='uvm_executor', help='uvm executor name')
    parser.add_argument('--soc_output', default=None,
                        help='soc output file name')
    parser.add_argument('--soc_cooperative',
                        action='store_true', help='soc cooperative')
    parser.add_argument('--soc_cooperative_hosted', action='store_true',
                        help='soc copoerative hosted based on pthread')
    parser.add_argument('--soc_preemptive', action='store_true')
    parser.add_argument('--debug', action='store_true')
    # return parser
    # options = parser.parse_args()
    # return options

# run action
# more readable


def Do(act: Action) -> None:
    if act.c_decl:
        global_ctx.graph.AddCDecl(act.c_decl)
    if act.c_headers:
        global_ctx.graph.AddCHeaders(act.c_headers)
    if act.c_header:
        global_ctx.graph.AddCHeader(act.c_header)
    # activity_method = getattr(self, 'Activity')
    # body_method = getattr(self, 'Body')
    if hasattr(act, 'Activity'):
        # assert(callable(activity_method))
        with CompoundActionScope(act):
            act.Activity()
    else:
        # assert(callable(body_method))
        with AtomicActionScope(act) as target_node:
            act.Body()
            target_node.c_src = act.c_src
            target_node.sv_src = act.sv_src
            target_node.executor_id = act.executor_id

    for dep in act.deps:
        act.scope.init_node.AddPredecessor(dep.scope.final_node)


def Run(act, args: argparse.Namespace) -> None:
    global_ctx.num_executors = args.num_executors

    logger.info(f'Do {act.name}')
    Do(act)

    global_ctx.graph.num_executors = args.num_executors

    logger.info(f'removing non-target nodes')
    global_ctx.graph.RemoveNonTargetNodes()
    logger.info(f'assigning sn')
    global_ctx.graph.AssignSN()
    logger.info('transtive reducing')
    global_ctx.graph.TransitiveReduction()
    # global_ctx.graph.AssignExecutorRandom()
    logger.info(f'assigning executor')
    global_ctx.graph.AssignExecutorSpread()
    logger.info(f'dump json')
    global_ctx.graph.DumpJson(args.graph_output)

    if args.uvm_output is not None:
        dag.UvmBackendGenF(global_ctx.graph, args.uvm_executor_name,
                           f'{args.uvm_output}', args.uvm_pkg_name)

    if args.soc_output is not None:
        if args.soc_cooperative:
            logger.debug(
                f'soc cooperative hosted: {args.soc_cooperative_hosted}')
            dag.CooperativeCBackendGenF(
                global_ctx.graph, args.soc_cooperative_hosted, False, f'{args.soc_output}', args.debug)
        else:
            dag.PreemptiveCBackendGenF(
                global_ctx.graph, True, f'{args.soc_output}')

def num_executors() -> int:
    return global_ctx.num_executors

# utils
def _Rand8(signed: bool = False) -> int:
    if signed:
        return random.randrange(-128, 128)
    else:
        return random.randrange(0, 256)


def _Rand16(signed: bool = False) -> int:
    bs = bytearray(2)
    for i in range(2):
        bs[i] = random.randrange(0, 256)
    return int.from_bytes(bs, 'little', signed=signed)


def _Rand32(signed: bool = False) -> int:
    bs = bytearray(4)
    for i in range(4):
        bs[i] = random.randrange(0, 256)
    return int.from_bytes(bs, 'little', signed=signed)


def _Rand64(signed: bool = False) -> int:
    bs = bytearray(8)
    for i in range(8):
        bs[i] = random.randrange(0, 256)
    return int.from_bytes(bs, 'little', signed=signed)


def _RandInt(bw: int, signed: bool = False) -> int:
    match bw:
        case 8:
            return _Rand8(signed)
        case 16:
            return _Rand16(signed)
        case 32:
            return _Rand32(signed)
        case 64:
            return _Rand64(signed)


def RandU8() -> int:
    return _Rand8(False)


def RandU16() -> int:
    return _Rand16(False)


def RandU32() -> int:
    return _Rand32(False)


def RandU64() -> int:
    return _Rand64(False)


def RandUInt(bw: int) -> int:
    return _RandInt(bw, False)


def RandS8() -> int:
    return _Rand8(True)


def RandS16() -> int:
    return _Rand16(True)


def RandS32() -> int:
    return _Rand32(True)


def RandS64() -> int:
    return _Rand64(True)


def RandInt(bw: int) -> int:
    return _RandInt(bw, True)


def RandBytes(s: int) -> bytes:
    r = bytearray(s)
    for i in range(s):
        r[i] = random.randrange(0, 256)
    return bytes(r)
