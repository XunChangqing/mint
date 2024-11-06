from purslane.aarch64 import v8
import logging
import purslane.addr_space
import random
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

        with v8.proc('rand_proc', f):
            for i in range(random.randrange(4, 20)):
                v8.arithm_imm()

            for i in range(random.randrange(4, 20)):
                v8.arithm_shifted_reg()

            v8.verbatim('mov x1, #1')

            with v8.reserve([v8.Reg.R1]):
                for i in range(random.randrange(4, 20)):
                    v8.arithm_imm()

if __name__ == '__main__':
    main()
