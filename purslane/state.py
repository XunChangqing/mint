#  Copyright 2024 zuoqian, zuoqian@qq.com


import random


class Context:
    def __init__(self) -> None:
        self.transition_ctrl_dict = {}


global_ctx = Context()


class TransitionCtrl:
    def __init__(self) -> None:
        self.trns_acts = []
        self.trns_table: dict[any, list[any]] = {}

    def AddTrnsAct(self, trns_act, src, dst) -> None:
        self.trns_acts.append(trns_act)

        # print(hasattr(trns_act, '_state_src'))
        # src = trns_act._state_src
        # dst = trns_act._state_dst

        if dst not in self.trns_table:
            self.trns_table[dst] = []
        self.trns_table[dst].append(trns_act)

    def ToInitiative(self, cs, init_state) -> list[any]:
        # find a path to a initiative action from current state(cs)
        visited = set()
        # action path
        path: list[any] = []
        state_stack: list[any] = []
        state_stack.append(cs)

        while len(state_stack) > 0:
            cur_state = state_stack[-1]

            next_tr = None
            for tr in self.trns_table[cur_state]:
                if tr not in visited:
                    next_tr = tr
                    break

            if next_tr is None:
                state_stack.pop()
                path.pop()
            else:
                visited.add(next_tr)
                path.append(next_tr)
                state_stack.append(next_tr._state_src)
                if next_tr._state_src == init_state:
                    return path

        raise "cannot find a path to a initiative state"

    # reverse
    def Infer(self, dest_state, num_trns: int, init_state) -> list[any]:
        tr_list = []
        cur_state = dest_state
        for i in range(num_trns):
            trs = self.trns_table[cur_state]
            assert (len(trs) > 0)
            tr = random.choice(trs)
            tr_list.append(tr)
            cur_state = tr._state_src

        if tr._state_src != init_state:
            toi_trs = self.ToInitiative(cur_state, init_state)
            tr_list.extend(toi_trs)

        # reverse
        return tr_list[::-1]


def StateTransition(src, dst):
    src_cls = src.__class__
    dst_cls = dst.__class__
    assert (src_cls is dst_cls)

    def StateTransitionDec(cls):
        assert (not hasattr(cls, '_state_src'))
        assert (not hasattr(cls, '_state_dst'))
        cls._state_src = src
        cls._state_dst = dst

        if src.__class__ not in global_ctx.transition_ctrl_dict:
            global_ctx.transition_ctrl_dict[src.__class__] = TransitionCtrl()

        trns_ctrl = global_ctx.transition_ctrl_dict[src.__class__]
        trns_ctrl.AddTrnsAct(cls, src, dst)
        return cls

    return StateTransitionDec


def StateInfer(dest_state, num_trns: int, init_state) -> list[any]:
    init_state_cls = init_state.__class__
    dest_state_cls = dest_state.__class__
    assert (init_state_cls is dest_state_cls)

    trns_ctrl = global_ctx.transition_ctrl_dict[dest_state_cls]
    return trns_ctrl.Infer(dest_state, num_trns, init_state)
