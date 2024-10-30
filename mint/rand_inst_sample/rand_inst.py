from purslane.aarch64 import instr_stream
from purslane.aarch64 import instr_pkg
from purslane.aarch64.isa import v8
from purslane.aarch64.isa.instr import Instr as AArch64Instr
import purslane.aarch64.isa.v8
import vsc
import logging
import purslane.addr_space
import ivy_app_cfg

logging.basicConfig(level=logging.INFO)


def main():
    addr_space = purslane.addr_space.AddrSpace()
    for mr in ivy_app_cfg.free_mem_ranges:
        addr_space.AddNode(mr.base, mr.size, mr.numa_id)

    scratch_memory_size = 64*1024
    scratch_memory = addr_space.Alloc(scratch_memory_size, 64)

    with open('rand_proc.S', 'w') as f:
        f.write('#include <linux/linkage.h>\n')
        f.write('.pushsection .text.rand_proc, "ax"\n')
        f.write('ENTRY(rand_proc)\n')

        push_stack_str = instr_stream.PushStackStream()
        push_stack_seq = push_stack_str.gen_seq()
        pop_stack_str = instr_stream.PopStackStream()
        pop_stack_seq = pop_stack_str.gen_seq()

        for inst in push_stack_seq:
            f.write(f'\t{inst.convert2asm()}\n')

        lsstr = instr_stream.RandLoadStoreStream()
        lsstr.page_addr = scratch_memory
        lsstr.page_size = scratch_memory_size
        lsstr.randomize()
        seq = lsstr.gen_seq(128)

        for inst in seq:
            f.write(f'\t{inst.convert2asm()}\n')

        for inst in pop_stack_seq:
            f.write(f'\t{inst.convert2asm()}\n')

        f.write('\tret\n')

        f.write('ENDPROC(rand_proc)\n')
        f.write('.popsection')


if __name__ == '__main__':
    main()
