# author : zuoqian
# Copyright 2024. All rights reserved.
from purslane.aarch64 import v8
from purslane.aarch64.v8 import Reg

# lock with load exclusive acquire and store exclusive release
# 使用 load-exclusive-acquire/store-exclusive-release 实现的简单锁


def lock_acq_excl_pair64(la: Reg, tr25: Reg, tr27: Reg, tr28: Reg):
    # la lock address
    # tr25-28 temporary registers
    # pair lock 使用2个寄存器保持 LOCK(1)/UNLOCK(0) 状态
    # x3 lock address
    # w25, w26 for 1, w27,w28 as target registers of load, w29 as status result register of the store exclusive
    v8.mov64_imm(tr25, 1)
    v8.verbatim(f'prfm pstl1keep, [{la.v64}]')
    v8.label('1')
    v8.ldaxp64(tr27, tr28, la)
    v8.cbnz64(tr27, '1b')
    v8.cbnz64(tr28, '1b')
    v8.stxp64(tr27, tr25, tr25, la)
    v8.cbnz32(tr27, '1b')


def unlock_rel_excl_pair64(la: Reg, tr25: Reg, tr27: Reg, tr28: Reg):
    # la lock address
    v8.mov64_imm(tr25, 0)
    v8.label('1')
    v8.ldaxp64(tr27, tr28, la)
    # 两个值都必须为1，否则发生错误
    v8.cbz64(tr27, '2f')
    v8.cbz64(tr28, '2f')
    v8.stlxp64(tr27, tr25, tr25, la)
    v8.cbnz32(tr27, '1b')
    v8.verbatim(f'b 3f')
    v8.label('2')
    v8.mov64_imm(Reg.R0, 1)
    v8.verbatim('bl xrt_exit')
    v8.label('3')


def lock_acq_excl_pair32(la: Reg, tr25: Reg, tr27: Reg, tr28: Reg):
    # la lock address
    # tr25-28 temporary registers
    # pair lock 使用2个寄存器保持 LOCK(1)/UNLOCK(0) 状态
    # x3 lock address
    # w25, w26 for 1, w27,w28 as target registers of load, w29 as status result register of the store exclusive
    v8.mov32_imm(tr25, 1)
    v8.verbatim(f'prfm pstl1keep, [{la.v64}]')
    v8.label('1')
    v8.ldaxp32(tr27, tr28, la)
    v8.cbnz32(tr27, '1b')
    v8.cbnz32(tr28, '1b')
    v8.stxp32(tr27, tr25, tr25, la)
    v8.cbnz32(tr27, '1b')


def unlock_rel_excl_pair32(la: Reg, tr25: Reg, tr27: Reg, tr28: Reg):
    # la lock address
    v8.mov32_imm(tr25, 0)
    v8.label('1')
    v8.ldaxp32(tr27, tr28, la)
    # 两个值都必须为1，否则发生错误
    v8.cbz32(tr27, '2f')
    v8.cbz32(tr28, '2f')
    v8.stlxp32(tr27, tr25, tr25, la)
    v8.cbnz32(tr27, '1b')
    v8.verbatim(f'b 3f')
    v8.label('2')
    v8.mov64_imm(Reg.R0, 1)
    v8.verbatim('bl xrt_exit')
    v8.label('3')


def lock_acq_excl_r64(la: Reg, tr25: Reg, tr27: Reg):
    # la lock address
    v8.mov64_imm(tr25, 1)
    v8.verbatim(f'prfm pstl1keep, [{la.v64}]')
    v8.label('1')
    v8.ldaxr64(tr27, la)
    v8.cbnz64(tr27, '1b')
    v8.stxr64(tr27, tr25, la)
    v8.cbnz32(tr27, '1b')


def lock_acq_excl_r32(la: Reg, tr25: Reg, tr27: Reg):
    # la lock address
    v8.mov32_imm(tr25, 1)
    v8.verbatim(f'prfm pstl1keep, [{la.v64}]')
    v8.label('1')
    v8.ldaxr32(tr27, la)
    v8.cbnz32(tr27, '1b')
    v8.stxr32(tr27, tr25, la)
    v8.cbnz32(tr27, '1b')


def lock_acq_excl_r16(la: Reg, tr25: Reg, tr27: Reg):
    # la lock address
    v8.mov32_imm(tr25, 1)
    v8.verbatim(f'prfm pstl1keep, [{la.v64}]')
    v8.label('1')
    v8.ldaxrh(tr27, la)
    v8.cbnz32(tr27, '1b')
    v8.stxrh(tr27, tr25, la)
    v8.cbnz32(tr27, '1b')


def lock_acq_excl_r8(la: Reg, tr25: Reg, tr27: Reg):
    # la lock address
    v8.mov32_imm(tr25, 1)
    v8.verbatim(f'prfm pstl1keep, [{la.v64}]')
    v8.label('1')
    v8.ldaxrb(tr27, la)
    v8.cbnz32(tr27, '1b')
    v8.stxrb(tr27, tr25, la)
    v8.cbnz32(tr27, '1b')


def unlock_rel_excl_r64(la: Reg):
    # la lock address
    v8.stlr64(Reg.ZERO, la)


def unlock_rel_excl_r32(la: Reg):
    # la lock address
    v8.stlr32(Reg.ZERO, la)


def unlock_rel_excl_r16(la: Reg):
    # la lock address
    v8.stlrh(Reg.ZERO, la)


def unlock_rel_excl_r8(la: Reg):
    # la lock address
    v8.stlrb(Reg.ZERO, la)


# lock with load-exclusive and store-exclusive and dmb
# 使用 load-exclusive/store-exclusive 配合 dmb 维序的简单锁
def lock_dmb_excl_pair64(la: Reg, tr25: Reg, tr27: Reg, tr28: Reg):
    # la lock address
    # tr25-28 temporary registers
    # pair lock 使用2个寄存器保持 LOCK(1)/UNLOCK(0) 状态
    # x3 lock address
    # w25, w26 for 1, w27,w28 as target registers of load, w29 as status result register of the store exclusive
    v8.mov64_imm(tr25, 1)
    v8.verbatim(f'prfm pstl1keep, [{la.v64}]')
    v8.label('1')
    v8.ldxp64(tr27, tr28, la)
    v8.cbnz64(tr27, '1b')
    v8.cbnz64(tr28, '1b')
    v8.stxp64(tr27, tr25, tr25, la)
    v8.cbnz32(tr27, '1b')
    v8.dmb()


def unlock_dmb_excl_pair64(la: Reg, tr25: Reg, tr27: Reg, tr28: Reg):
    # la lock address
    v8.mov64_imm(tr25, 0)
    v8.label('1')
    v8.ldaxp64(tr27, tr28, la)
    # 两个值都必须为1，否则发生错误
    v8.cbz64(tr27, '2f')
    v8.cbz64(tr28, '2f')
    v8.dmb()
    v8.stxp64(tr27, tr25, tr25, la)
    v8.cbnz32(tr27, '1b')
    v8.verbatim(f'b 3f')
    v8.label('2')
    v8.mov64_imm(Reg.R0, 1)
    v8.verbatim('bl xrt_exit')
    v8.label('3')


def lock_dmb_excl_pair32(la: Reg, tr25: Reg, tr27: Reg, tr28: Reg):
    # la lock address
    # tr25-28 temporary registers
    # pair lock 使用2个寄存器保持 LOCK(1)/UNLOCK(0) 状态
    # x3 lock address
    # w25, w26 for 1, w27,w28 as target registers of load, w29 as status result register of the store exclusive
    v8.mov32_imm(tr25, 1)
    v8.verbatim(f'prfm pstl1keep, [{la.v64}]')
    v8.label('1')
    v8.ldxp32(tr27, tr28, la)
    v8.cbnz32(tr27, '1b')
    v8.cbnz32(tr28, '1b')
    v8.stxp32(tr27, tr25, tr25, la)
    v8.cbnz32(tr27, '1b')
    v8.dmb()


def unlock_dmb_excl_pair32(la: Reg, tr25: Reg, tr27: Reg, tr28: Reg):
    # la lock address
    v8.mov32_imm(tr25, 0)
    v8.label('1')
    v8.ldaxp32(tr27, tr28, la)
    # 两个值都必须为1，否则发生错误
    v8.cbz32(tr27, '2f')
    v8.cbz32(tr28, '2f')
    v8.dmb()
    v8.stxp32(tr27, tr25, tr25, la)
    v8.cbnz32(tr27, '1b')
    v8.verbatim(f'b 3f')
    v8.label('2')
    v8.mov64_imm(Reg.R0, 1)
    v8.verbatim('bl xrt_exit')
    v8.label('3')


def lock_dmb_excl_r64(la: Reg, tr25: Reg, tr27: Reg):
    # la lock address
    v8.mov64_imm(tr25, 1)
    v8.verbatim(f'prfm pstl1keep, [{la.v64}]')
    v8.label('1')
    v8.ldxr64(tr27, la)
    v8.cbnz64(tr27, '1b')
    v8.stxr64(tr27, tr25, la)
    v8.cbnz32(tr27, '1b')
    v8.dmb()


def lock_dmb_excl_r32(la: Reg, tr25: Reg, tr27: Reg):
    # la lock address
    v8.mov32_imm(tr25, 1)
    v8.verbatim(f'prfm pstl1keep, [{la.v64}]')
    v8.label('1')
    v8.ldaxr32(tr27, la)
    v8.cbnz32(tr27, '1b')
    v8.stxr32(tr27, tr25, la)
    v8.cbnz32(tr27, '1b')
    v8.dmb()


def lock_dmb_excl_r16(la: Reg, tr25: Reg, tr27: Reg):
    # la lock address
    v8.mov32_imm(tr25, 1)
    v8.verbatim(f'prfm pstl1keep, [{la.v64}]')
    v8.label('1')
    v8.ldaxrh(tr27, la)
    v8.cbnz32(tr27, '1b')
    v8.stxrh(tr27, tr25, la)
    v8.cbnz32(tr27, '1b')
    v8.dmb()


def lock_dmb_excl_r8(la: Reg, tr25: Reg, tr27: Reg):
    # la lock address
    v8.mov32_imm(tr25, 1)
    v8.verbatim(f'prfm pstl1keep, [{la.v64}]')
    v8.label('1')
    v8.ldaxrb(tr27, la)
    v8.cbnz32(tr27, '1b')
    v8.stxrb(tr27, tr25, la)
    v8.cbnz32(tr27, '1b')
    v8.dmb()


def unlock_dmb_excl_r64(la: Reg):
    # la lock address
    v8.dmb()
    v8.stlr64(Reg.ZERO, la)


def unlock_dmb_excl_r32(la: Reg):
    # la lock address
    v8.dmb()
    v8.stlr32(Reg.ZERO, la)


def unlock_dmb_excl_r16(la: Reg):
    # la lock address
    v8.dmb()
    v8.stlrh(Reg.ZERO, la)


def unlock_dmb_excl_r8(la: Reg):
    # la lock address
    v8.dmb()
    v8.stlrb(Reg.ZERO, la)

# locks implemented with atomic instructions with acquire/release semantics
# 使用带acquire/release 语义的原子指令实现的简单锁

# locks with atomic and dmb instructions
# 使用原子指令和dmb实现的简单锁


# 使用带 acquire和release 语言的exclusive指令实现的 ticket lock
# r32 表示next和current加起来32bit
def ticket_lock_acq_excl_r32(x1: Reg, w5: Reg, w6: Reg):
    # x1 lock address
    # w5 current ticket
    # w6 next ticket, should be reserved for releasing
    # w6记录下一个，该寄存器值调用者需要保留，释放锁时需要
    v8.verbatim(f'prfm pstl1keep, [{x1.v64}]')
    v8.label('1')
    v8.ldaxr32(w5, x1)
    v8.add32_imm(w5, w5, 0x10000)
    v8.stxr32(w6, w5, x1)
    v8.cbnz32(w6, '1b')
    v8.and32_imm(w6, w5, 0xFFFF)
    v8.cmp32_reg(w6, w5, v8.ShiftType.LSR, 16)
    v8.beq('3f')
    v8.label('2')
    v8.ldaxrh(w6, x1)
    v8.cmp32_reg(w6, w5, v8.ShiftType.LSR, 16)
    v8.bne('2b')
    v8.label('3')


def ticket_unlock_rel_excl_r32(la: Reg, w6: Reg):
    # la lock address
    # w6 next ticket
    v8.add32_imm(w6, w6, 1)
    v8.stlrh(w6, la)


def bakery_lock_acq_a64():
    #  <!-- F.3.1 Acquiring a bakery lock
    #  Parameters:
    #    X4: my thread index
    #    X5: number of threads
    #    X6: flag address (flags = choosing)
    #    X7: label address (label = numbers)
    #  Used https://www.geeksforgeeks.org/bakery-algorithm-in-process-synchronization/ as reference for pseudo code
    #  additional registers used - 24-29
    #  -->
    pass


def bakery_lock_release_a64():
    pass
