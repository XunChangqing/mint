from enum import Enum
import io
import typing
import typing_extensions
import dataclasses
import json
import re
import logging
import random
from typing import List
logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Executor:
    id: int


class Node:
    def __init__(self, name: str, preds: typing.List[typing_extensions.Self] = None, pred: typing_extensions.Self = None):
        self.name = name
        self.sn = 0
        self.executor_id = None
        self.is_target = False
        self.c_src = None
        self.sv_src = None
        self.predecessors: typing.List[Node] = []
        self.successors: typing.List[Node] = []
        self.all_predecessors: typing.Dict[int, Node] = []
        self.all_predecessor_hops: typing.Dict[int, int] = []

        # for traversing in topological order
        self.preds_left = 0

        # for uvm generation
        self.uvm_name = ''
        self.uvm_class_name = ''

        # for c generation
        self.sn_in_thread = 0
        self.thread_id = 0
        self.body_func_name = ''

        if preds:
            self.predecessors = preds

        if pred:
            self.predecessors.append(pred)

    def AddPredecessor(self, act: typing_extensions.Self):
        if act is None:
            return

        if act not in self.predecessors:
            self.predecessors.append(act)

    def DelPredecessor(self, act: typing_extensions.Self):
        self.predecessors.remove(act)

    def Predecessors(self) -> typing.Generator[typing_extensions.Self, None, None]:
        for p in self.predecessors:
            yield p

    # def AllPredecessors(self) -> typing.Generator[typing_extensions.Self, None, None]:
    #   # clone, otherwise the original list will be corrupted
    #   preds = self.predecessors[:]
    #   while len(preds) > 0:
    #     back = preds.pop()
    #     preds = preds + back.predecessors
    #     # logger.debug(f'all pred gen {preds} {back.name} {len(back.predecessors)}')
    #     yield back

    def UpdateAllPredecessors(self):
        self.all_predecessors = {node.sn: node for node in self.predecessors}
        for pred in self.predecessors:
            self.all_predecessors.update(pred.all_predecessors)

        # self.all_predecessor_hops = {node.sn:1 for node in self.predecessors}
        # for pred in self.predecessors:
        #     pass

    def NumPredecessors(self) -> int:
        return len(self.predecessors)

    def UpdateSuccessors(self):
        self.successors.clear()
        for p in self.predecessors:
            p.AddSuccessor(self)

    def AddSuccessor(self, act: typing_extensions.Self):
        if act not in self.successors:
            self.successors.append(act)

    def DelSuccessor(self, node: typing_extensions.Self):
        if node in self.successors:
            self.successors.remove(node)

    def Successors(self) -> typing.Generator[typing_extensions.Self, None, None]:
        for s in self.successors:
            yield s

    def NumSuccessors(self) -> int:
        return len(self.successors)


class ExecutorAssignPolicy(Enum):
    SPREAD = 1
    RANDOM = 2


class Graph:
    def __init__(self, num_executors: int = 2):
        self.nodes: typing.List[Node] = []
        self.num_executors = num_executors
        self.c_headers: typing.List[str] = []
        self.c_decls: typing.List[str] = []

    def AddNode(self, node):
        self.nodes.append(node)

    def AddCDecl(self, c_decl: str):
        self.c_decls.append(c_decl)

    def AddCHeader(self, c_header: str):
        self.c_headers.append(c_header)

    def AddCHeaders(self, c_headers: typing.List[str]):
        self.c_headers.extend(c_headers)

    def NumNodes(self) -> int:
        return len(self.nodes)

    def Nodes(self) -> typing.Generator[Node, None, None]:
        for node in self.nodes:
            yield node

    def NodesInTopoOrder(self, in_random: bool = False) -> typing.Generator[Node, None, None]:
        self.UpdateSuccessors()

        ready_nodes = []
        for node in self.nodes:
            node.preds_left = len(node.predecessors)
            if node.preds_left <= 0:
                ready_nodes.append(node)

        while len(ready_nodes) > 0:
            ridx = 0
            if in_random:
                ridx = random.randrange(0, len(ready_nodes))
            front = ready_nodes.pop(ridx)
            yield front
            for succ in front.Successors():
                succ.preds_left -= 1
                if succ.preds_left <= 0:
                    ready_nodes.append(succ)

    def CheckCyclic(self):
        pass

    def UpdateSuccessors(self):
        for node in self.nodes:
            node.UpdateSuccessors()

    def UpdateAllPredecessors(self):
        for node in self.NodesInTopoOrder():
            node.UpdateAllPredecessors()

    def RemoveNonTargetNodes(self):
        self.UpdateSuccessors()

        for node in self.nodes:
            if not node.is_target:
                for succ in node.Successors():
                    succ.DelPredecessor(node)
                    for pred in node.predecessors:
                        succ.AddPredecessor(pred)

        nodes = []
        for node in self.nodes:
            if node.is_target:
                logger.debug(f'append target {node.name}')
                nodes.append(node)
            else:
                logger.debug(f'remove node {node.name}')
        self.nodes = nodes

    def AssignSN(self):
        sn = 0
        for n in self.nodes:
            n.sn = sn
            sn = sn + 1

    def TransitiveReduction(self):
        # TODO
        # naive implemetation
        self.UpdateAllPredecessors()

        for node in self.nodes:
            preds = node.predecessors[:]
            for pr in node.predecessors:
                for ppr in node.predecessors:
                    if pr.sn in ppr.all_predecessors:
                        preds.remove(pr)
                        break
            node.predecessors = preds

    def AssignExecutor(self, num_executors: int = 2, policy: ExecutorAssignPolicy = ExecutorAssignPolicy.SPREAD):
        if policy == ExecutorAssignPolicy.SPREAD:
            self.AssignExeuctorSpread()
        else:
            self.AssignExecutorRandom()

    def AssignExecutorSpread(self):
        seq = []

        for node in self.NodesInTopoOrder():
            if node.executor_id is None:
                if len(seq) <= 0:
                    seq = random.sample(
                        range(self.num_executors), self.num_executors)
                node.executor_id = seq.pop()

    def AssignExecutorRandom(self):
        for node in self.nodes:
            if node.executor_id is None:
                node.executor_id = random.randrange(0, self.num_executors)

    def DumpJson(self, fname: str):
        json_dict = {
            'sv_headers': [],
            'c_headers': self.c_headers,
            'c_decls': self.c_decls,
            'actions': [],
            'executors': []
        }

        for i in range(self.num_executors):
            json_dict['executors'].append({'id': i})

        for node in self.nodes:
            node_dict = {
                'sn': node.sn,
                'executor_id': node.executor_id,
                # 'executor_id': 0,
                'c_src': node.c_src,
                'sv_src': node.sv_src,
                'name': node.name,
                'predecessors': []
            }
            for pred in node.predecessors:
                node_dict['predecessors'].append(pred.sn)

            json_dict['actions'].append(node_dict)

        with open(fname, 'w') as f:
            json.dump(json_dict, f, indent=2)

    def LoadJson(fname: str):
        pass


class Thread:
    def __init__(self, id: int):
        self.id = id
        self.nodes: List[Node] = []


class Core:
    def __init__(self, id: int):
        self.id = id
        self.threads: List[Thread] = []


def CBackendThreadAssign(graph: Graph) -> typing.List[Core]:
    graph.UpdateAllPredecessors()

    cores = [Core(id=i) for i in range(graph.num_executors)]

    # 随机序遍历，使得无关 action 在线程内的排序随机
    logger.info(
        f'assign actions to threads, number of nodes {len(graph.nodes)}')
    for node in graph.NodesInTopoOrder(in_random=True):
        logger.debug(f'thread assign node {node.name} {id(node):#x}')
        eid = node.executor_id
        core = cores[eid]

        # 必须满足条件:
        # 所分配线程的最后一个 action 必须为当前 action的前序（递归）
        # 这保证了 thread 内所有 action 都是有依赖关系的
        # 反之，这也保证了没有依赖关系的 action 不会在同一个线程内

        # 按照 topological 序遍历图，保证在访问一个 action 时，其所有前序都已经
        # 访问过，此时检查是否将当前 action 加入已经建立的线程，条件是
        # 该线程的最末 action 是当前 action 的前序，
        # 1. 加入同一个线程，约束了执行顺序，所以必须有依赖
        # 2. 之所以不要求是直接前序，是因为其直接前序可能 executor 不同

        # 总是先线程号 0 开始查找，尽量都分配到线程 0
        # 如果不存在符合条件的，则必须新建线程

        assigned_in_existing_thread = False
        for thd in core.threads:
            assert (len(thd.nodes) > 0)
            back = thd.nodes[-1]

            # logger.debug(f'thd nodes {thd.nodes}')
            if back.sn in node.all_predecessors:
                assigned_in_existing_thread = True

                node.thread_id = thd.id
                node.sn_in_thread = len(thd.nodes)

                thd.nodes.append(node)

            if assigned_in_existing_thread:
                break

        if not assigned_in_existing_thread:
            core.threads.append(Thread(len(core.threads)))
            thd = core.threads[-1]
            thd.nodes.append(node)

            node.thread_id = thd.id
            node.sn_in_thread = 0

    return cores


def CooperativeCBackendGenF(graph: Graph, hosted: bool, core_binding: bool, fname: str, debug: bool):
    with open(fname, 'w') as f:
        CooperativeCBackendGen(graph, hosted, core_binding, f, debug)


def CooperativeCBackendGen(graph: Graph, hosted: bool, core_binding: bool, f: io.TextIOWrapper, debug: bool):
    logger.info('cooperative backend generating')

    cores = CBackendThreadAssign(graph)

    f.write('// generated by mango\n')
    f.write('\n')

    if hosted:
        # defined by gcc builtins
        # portable among different processors
        f.write('#define smp_mb() __atomic_thread_fence(__ATOMIC_ACQ_REL)\n')
        f.write('#define smp_rmb() __atomic_thread_fence(__ATOMIC_ACQUIRE)\n')
        f.write('#define smp_wmb() __atomic_thread_fence(__ATOMIC_RELEASE)\n')
    else:
        #  aarch64 only
        f.write('#define dmb(opt) asm volatile(\"dmb \" #opt : : : \"memory\")\n')
        f.write('#define smp_mb() dmb(ish)\n')
        f.write('#define smp_rmb() dmb(ishld)\n')
        f.write('#define smp_wmb() dmb(ishst)\n')

    f.write('#include <stdint.h>\n')

    if hosted:
        f.write('#include <pthread.h>\n')
        f.write('#include <sched.h>\n')
        f.write('#include <unistd.h>\n')
        f.write('#include <stdio.h>\n')

    #  headers
    if len(graph.c_headers) > 0:
        f.write('// headers\n')
        for header in graph.c_headers:
            f.write(f'{header}\n')
    
    if len(graph.c_decls) > 0:
        f.write('// declarations\n')
        for decl in graph.c_decls:
            f.write(f'{decl}\n')

    f.write('\n')

    # 生成所有 action 的 body 函数
    logger.info('generate body functions of all actions')
    f.write('// body functions of actions\n\n')
    for node in graph.nodes:
        f.write(f'// body function of action {node.name}\n')

        name = re.sub('\\.', '_',  node.name)
        node.body_func_name = f'{name}_body_func'
        f.write(f'static uint32_t {node.body_func_name}(uint32_t state){{\n')
        if debug:
            f.write(f'printf("{node.name}\\n");')
        f.write(f'{node.c_src}')
        f.write('\n')
        f.write('return 0;\n')
        f.write('}\n')

    f.write('\n\n')

    # 线程、action状态变量声明
    for core in cores:
        num_active_threads_var = f'num_active_threads_core_{core.id}'
        f.write(f'uint32_t {num_active_threads_var} = {len(core.threads)};\n')
        for thd in core.threads:
            # 每个线程两个全局状态变量
            # 线程状态
            # action状态
            thd_name = f'core_{core.id}_thread_{thd.id}'
            thread_state_var = f'{thd_name}_thread_state'
            action_state_var = f'{thd_name}_action_state'
            # 线程状态变量，核间通信，使用 volatile 修饰
            f.write(f'volatile uint32_t {thread_state_var} = 0;\n')
            # 线程内当前 action 状态，不需要 volatile 修饰
            f.write(f'uint32_t {action_state_var} = 0;\n')

    f.write('\n\n')

    logger.info('generate thread functions of all cores')
    # 为每个线程生成函数
    for cc in cores:
        # 记录目前剩余活跃线程数 n+1，使用无符号整数，判断大于 0
        num_active_threads_var = f'num_active_threads_core_{cc.id}'

        # 生成处理核内每个线程主函数
        for thd in cc.threads:
            # 每个线程两个全局状态变量
            # 线程状态
            # action状态
            thd_name = f'core_{cc.id}_thread_{thd.id}'
            thread_state_var = f'{thd_name}_thread_state'
            action_state_var = f'{thd_name}_action_state'

            # 线程主函数
            f.write(f'void {thd_name}_func(){{\n')

            # switch，根据状态调用指定 action body 函数
            f.write(f'switch({thread_state_var}){{\n')

            for act in thd.nodes:
                f.write(f'case {act.sn_in_thread}:\n')
                # 等待前序条件，所有与自身不在同一线程的前序 action，
                # 不在同一个处理核，或是线程不同
                conds = []
                for pred in act.predecessors:
                    if pred.executor_id != cc.id or pred.thread_id != thd.id:
                        pred_thread_state_var = f'core_{pred.executor_id}_thread_{pred.thread_id}_thread_state'
                        f.write(
                            f'// wait for {pred.name} @ core {pred.executor_id} thread {pred.thread_id}\n')
                        conds.append(
                            f'{pred_thread_state_var} <= {pred.sn_in_thread}')

                if len(conds) > 0:
                    f.write('if(')
                    # 只要一个条件满足，即有前序 action 未完成，立即 return
                    # 释放控制权，后续重试
                    first = True
                    for c in conds:
                        if not first:
                            f.write(' || ')

                        f.write(c)
                        first = False

                    f.write('){\n')
                    f.write('return;\n')
                    f.write('}\n')

                    # 使用 dmb ld
                    # 否则需要对所有判断的线程状态变量使用有 aquire 语义的 load 指令
                    # barrier 只需要一个
                    f.write('smp_rmb();\n')

                f.write(
                    f'{action_state_var} = {act.body_func_name}({action_state_var});\n')
                f.write('break;\n')

            # 最后一个 action 结束以后
            f.write(f'case {len(thd.nodes)}:\n')
            # 标志线程结束
            f.write(f'{num_active_threads_var}--;\n')
            # 允许状态再次增加，以便下次进入 default
            f.write('break;\n')

            f.write('default:\n')
            f.write('return;\n')

            f.write('}\n')

            # 如果 action 完成，线程状态+1，执行下一个 action
            f.write(f'if({action_state_var} == 0){{\n')
            # 调用特殊写函数，支持核间同步
            f.write(f'{thread_state_var}++;\n')
            f.write('smp_wmb();\n')
            # dmb st，调用 store 的 dmb 维持存储序
            # 或者对 thread_state_var 的修改使用 store release 语义的保存指令
            f.write('}\n')

            f.write('}\n\n')

    for cc in cores:
        # 记录目前剩余活跃线程数 n+1，使用无符号整数，判断大于 0
        num_active_threads_var = f'num_active_threads_core_{cc.id}'
        # main function of the core
        f.write(f'void core_{cc.id}_func(){{\n')

        f.write(f'while({num_active_threads_var} > 0){{\n')

        # 生成处理核内每个线程主函数
        for thd in cc.threads:
            f.write(f'core_{cc.id}_thread_{thd.id}_func();\n')

        f.write("}\n")
        f.write("}\n\n")

    # 生成一个根据输入 core id 自动进入不同函数的函数，便于裸机环境自动调用
    f.write('void mango_core_main_func(uint64_t core_id){\n')
    f.write('switch(core_id){\n')

    for cc in cores:
        f.write(f'case {cc.id}:\n')
        f.write(f'core_{cc.id}_func();\n')
        f.write('break;\n')

    f.write('default:\n')
    f.write('break;\n')
    f.write('}\n')

    f.write('}\n\n')

    # hosted 环境一并将启动代码生成完毕
    # 主函数 mango_main
    # 每个处理核一个线程
    if hosted:
        f.write('#include <stdlib.h>\n')

        f.write('void mango_main(){\n')
        f.write('int ret;\n')

        # 每个处理核建立一个线程，绑定到指定处理核，入口函数为对应处理核函数
        for i in range(len(cores)):
            f.write(f'pthread_t thread_id_{i};\n')
            f.write(f'pthread_attr_t attr_{i};\n')
            f.write(f'cpu_set_t cpu_set_{i};\n')

        f.write('\n')

        for i in range(len(cores)):
            f.write(f"pthread_attr_init(&attr_{i});\n")
            if core_binding:
                f.write(f"CPU_ZERO(&cpu_set_{i});\n")
                f.write(f"CPU_SET({i}, &cpu_set_{i});\n")
                f.write(
                    f'pthread_attr_setaffinity_np(&attr_{i}, sizeof(cpu_set_t), &cpu_set_{i});\n')

            f.write(
                f'ret = pthread_create(&thread_id_{i}, &attr_{i}, (void*(*)(void*))core_{i}_func, NULL);\n')
            f.write('if(ret != 0){\n')
            f.write('printf(\"failed to pthread_create\\n\");\n')
            f.write('exit(1);\n')
            f.write('}\n')

        f.write('\n')

        for i in range(len(cores)):
            f.write(f'pthread_join(thread_id_{i}, NULL);\n')

        f.write('}\n')


def PreemptiveCBackendGenF(graph: Graph, core_binding: bool, fname: str):
    with open(fname, 'w') as f:
        PreemptiveCBackenGen(graph, core_binding, f)


def PreemptiveCBackenGen(graph: Graph, core_binding: bool, f: io.TextIOWrapper):
    cores = CBackendThreadAssign(graph)
    f.write('// generated by mango\n')
    f.write('\n')

    f.write('#include <stdint.h>\n')
    f.write('#include <pthread.h>\n')
    f.write('#include <sched.h>\n')
    f.write('#include <unistd.h>\n')
    f.write('#include <stdio.h>\n')
    f.write('#include <stdlib.h>\n')

    # headers
    if len(graph.c_headers) > 0:
        f.write('// headers\n')
        for h in graph.c_headers:
            f.write(f'{h}\n')

    # 生成所有 action 的 body 函数
    f.write('// body functions of actions\n\n')
    for aa in graph.nodes:
        f.write(f'// body function of action {aa.name}\n')

        name = re.sub('\\.', '_', aa.name)
        aa.body_func_name = f'{name}_body_func'
        f.write(f'static void {aa.body_func_name}(){{\n')
        f.write(f'{aa.c_src}')
        f.write('}\n')
    f.write('\n\n')

    # 线程、action状态变量声明
    for cc in cores:
        for thd in cc.threads:
            prefix = f'core_{cc.id}_thread_{thd.id}_'
            # 每个线程
            # 锁
            f.write(
                f'pthread_mutex_t {prefix}mutex = PTHREAD_MUTEX_INITIALIZER;\n')
            # 条件变量
            f.write(
                f"pthread_cond_t {prefix}cond = PTHREAD_COND_INITIALIZER;\n")
            # 线程状态变量，不需要 volatile，通过 mutex 保护
            f.write(f"uint64_t {prefix}state = 0;\n")

            # 生成一个函数用于等待线程状态
            f.write(f"static void {prefix}wait(uint64_t ts){{\n")

            f.write(f'pthread_mutex_lock(&{prefix}mutex);\n')
            f.write(f'while({prefix}state <= ts){{\n')
            f.write(f'pthread_cond_wait(&{prefix}cond, &{prefix}mutex);\n')
            f.write('}\n')
            f.write(f'pthread_mutex_unlock(&{prefix}mutex);\n')

            f.write('}\n')

            # 生成线程状态前进函数
            f.write(f'static void {prefix}advance(){{\n')

            f.write(f'pthread_mutex_lock(&{prefix}mutex);\n')
            f.write(f'{prefix}state++;\n')
            f.write(f'pthread_cond_broadcast(&{prefix}cond);\n')
            f.write(f'pthread_mutex_unlock(&{prefix}mutex);\n')

            f.write('}\n')

    f.write('\n\n')

    # 生成线程函数
    for cc in cores:
        # 生成处理核内每个线程主函数
        for thd in cc.threads:
            prefix = f'core_{cc.id}_thread_{thd.id}_'

            # 线程主函数
            f.write(f'static void {prefix}func(){{\n')

            # 从前向后执行每个 action 函数即可
            for act in thd.nodes:
                f.write(f'// action {act.name}\n')

                # 等待前序条件，所有与自身不在同一线程的前序 action，只需要等待之间前序
                # 不在同一个处理核，或是线程不同
                conds = []
                for pred in act.predecessors():
                    # 等待与当前 action 处于不同线程的的前序 action
                    if pred.executor_id != cc.id or pred.thread_id != thd.id:
                        pred_prefix = f'core_{pred.executor_id}_thread_{pred.thread_id}_'
                        f.write(
                            f'// wait for {pred.name} @ core {pred.executor_id} thread {pred.thread_id}\n')
                        f.write(f'{pred_prefix}wait({pred.sn_in_thread});\n')

                # 调用 action body 函数
                f.write(f'{act.body_func_name}();\n')

                # 线程状态前进
                f.write(f'{prefix}advance();\n')

            f.write('}\n\n')

    f.write('\n')

    # 建立主入口函数，为每个线程建立一个 linux 线程，并绑定对应处理核
    f.write('void mango_main(){\n')
    f.write('int ret;\n')

    # 每个线程 id、attr、cpu_set
    for cc in cores:
        for thd in cc.threads:
            prefix = f'core_{cc.id}_thread_{thd.id}_'
            f.write(f"pthread_t {prefix}id;\n")
            f.write(f"pthread_attr_t {prefix}attr;\n")
            f.write(f"cpu_set_t {prefix}cpu_set;\n")

    f.write('\n')
    # 建立线程

    for cc in cores:
        # 生成处理核内每个线程主函数
        for thd in cc.threads:
            prefix = f"core_{cc.id}_thread_{thd.id}_"

            f.write(f'CPU_ZERO(&{prefix}cpu_set);\n')
            f.write(f'CPU_SET({cc.id}, &{prefix}cpu_set);\n')
            f.write(f'pthread_attr_init(&{prefix}attr);\n')
            f.write(
                f'pthread_attr_setaffinity_np(&{prefix}attr, sizeof(cpu_set_t), &{prefix}cpu_set);\n')
            f.write(
                f'ret = pthread_create(&{prefix}id, &{prefix}attr, (void*(*)(void*)){prefix}func, NULL);\n')
            f.write('if(ret != 0){\n')
            f.write('printf(\"failed to pthread_create\\n\");\n')
            f.write('exit(1);\n')
            f.write('}\n')

    f.write('\n')
    # 等待线程结束
    for cc in cores:
        # 生成处理核内每个线程主函数
        for thd in cc.threads:
            prefix = f'core_{cc.id}_thread_{thd.id}_'
            f.write(f'pthread_join({prefix}id, NULL);\n')

    f.write('}\n')


#  把 scheduler 也放进生成代码中，便于版本一致维护
UVM_ACTION_SCHEDULER_TMPL = """
class Action;
  int sn;
  string name;
  int executor_id;
  int num_predecessors;
  Action successors[];

  function new();
    sn = -1;
    name = "unknown";
    executor_id = -1;
    num_predecessors = 0;
  endfunction

  virtual task ExecBody({executor} exec);
  endtask
endclass

class ActionScheduler;
  {executor} executors[];
  Action actions[];
  int num_action_left;
  int progress_fd;

  function new({executor} executors[], Action actions[]);
    this.executors = executors;
    this.actions = actions;
    this.num_action_left = actions.size();
    this.progress_fd = $fopen("./mango_progress.txt", "w");
  endfunction

  task ExecAction(Action act);
    fork
      begin
        $fdisplay(this.progress_fd, "start %d", act.sn);
        $fflush(this.progress_fd);
        act.ExecBody(executors[act.executor_id]);
        $fdisplay(this.progress_fd, "end %d", act.sn);
        $fflush(this.progress_fd);
        // 完毕以后，所有后继 action 标记本 action 完成
        // 启动 ready 项
        foreach(act.successors [ i ]) begin
            Action succ = act.successors[i];
            succ.num_predecessors--;
            if(succ.num_predecessors <= 0) begin
                this.ExecAction(succ);
            end
        end

        // 修改未完成 action 数量
        num_action_left--;
      end
    join_none
  endtask

  task Run();
      // 启动所有 初始 action ，即初始就没有任何依赖的 action

      // 先选择，再运行，以免发生竞争
      Action init_actions[$];
      foreach(this.actions [ i ]) begin
          Action act = this.actions[i];
          if(act.num_predecessors <= 0) begin
              init_actions.push_back(act);
          end
      end

      foreach(init_actions [ i ]) begin
          Action act = init_actions[i];
          this.ExecAction(act);
      end

      // 等待所有 action 完成
      wait(num_action_left <= 0);

      $fclose(this.progress_fd);
  endtask
endclass
"""


def UvmBackendGenF(graph: Graph, executor_name: str, fname: str, pkg_name: str = None) -> None:
    with open(fname, 'w') as f:
        UvmBackendGen(graph, executor_name, f, pkg_name)


def UvmBackendGen(graph: Graph, executor_name: str, f, pkg_name: str = None) -> None:
    f.write('// generated by mango\n')
    f.write('\n')

    if pkg_name is not None:
        f.write(f'package {pkg_name};\n')

    f.write('import uvm_pkg::*;\n')
    f.write('`include \"uvm_macros.svh\"\n')

    f.write(UVM_ACTION_SCHEDULER_TMPL.format(executor=executor_name))

    f.write('\n')

    graph.UpdateSuccessors()

    # set action class name
    for node in graph.Nodes():
        uvm_name = re.sub('\.', '_', node.name)
        node.uvm_name = uvm_name
        node.uvm_class_name = f'{uvm_name}_Action'

    # declare all actions
    for node in graph.Nodes():
        assert (node.is_target)
        f.write(f'class {node.uvm_class_name} extends Action;\n')
        f.write(f'  virtual task ExecBody({executor_name} exec);\n')
        sv_src = node.sv_src
        if sv_src:
            f.write(sv_src)
            f.write('\n')
        f.write('  endtask\n')
        f.write('endclass\n')
        f.write('\n')

    f.write('class TestCase;\n')
    f.write('  ActionScheduler action_scheduler;\n')
    f.write('\n')
    f.write(f'  function new({executor_name} execs[]);\n')

    f.write(f'    Action actions[] = new[{graph.NumNodes()}];\n')
    f.write('\n')

    # new all actions
    for node in graph.Nodes():
        f.write(f'    {node.uvm_class_name} {node.uvm_name} = new;\n')

    i = 0
    for node in graph.Nodes():
        f.write(f'    {node.uvm_name}.sn = {node.sn};\n')
        f.write(f'    {node.uvm_name}.name = "{node.name}";\n')
        f.write(f'    {node.uvm_name}.executor_id = {node.executor_id};\n')
        f.write(
            f'    {node.uvm_name}.num_predecessors = {len(node.predecessors)};\n')
        f.write(f'    actions[{i}] = {node.uvm_name};\n')
        i += 1

    f.write('\n')

    # set successors of actions
    for node in graph.Nodes():
        if node.NumSuccessors() > 0:
            f.write(
                f'    {node.uvm_name}.successors = new[{node.NumSuccessors()}];\n')

            for j, succ in enumerate(node.Successors()):
                f.write(
                    f'    {node.uvm_name}.successors[{j}] = {succ.uvm_name};\n')

    f.write('    this.action_scheduler = new(execs, actions);\n')

    f.write('  endfunction\n')
    f.write('\n')

    f.write('  task Run();\n')
    f.write('    this.action_scheduler.Run();\n')
    f.write('  endtask\n')

    f.write('endclass\n')
    f.write('\n')

    if pkg_name is not None:
        f.write('endpackage\n')
