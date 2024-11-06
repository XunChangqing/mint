# author : zuoqian
# Copyright 2024. All rights reserved.

# 不同写入者写入不同地址，多个观察者，在 acquire-release 指令帮助下，观察到相同的顺序
# with acquire-release, multiple observers can observe writes to multiple locations
# in the same order. Please refer to DDI0487A_h_armv8_arm K10.2.4.


import ivy_app_cfg
import purslane
import logging
import random
import atexit
import io
import math

import purslane.addr_space

logger = logging.getLogger('aarch64_moesi')

# asm_f = open('mlmo_dat.S', 'w')
# asm_f.write('\t.section "data"\n')
# atexit.register(asm_f.close)

# P0 write A0
# P1 write A1
# P2 read A0, A1
# P3 read A1, A0


def main():
    nr_cpus = ivy_app_cfg.NR_CPUS
    if nr_cpus % 4 != 0:
        logger.critical('number of cpus must be a multiple of 4')
        raise 'number of cpus must be a multiple of 4'

    addr_space = purslane.addr_space.AddrSpace()
    for fr in ivy_app_cfg.FREE_RANGES:
        logger.info(f'addr space region: {fr[0]:#x}, {fr[1]:#x}')
        addr_space.AddNode(fr[0], fr[1]-fr[0]+1, fr[2])


    test_times = 2048
    batch_size = math.ceil(test_times/4)
    iter = 0
    end = batch_size
    # split output into 4 files, to speed up compilation
    for fi in range(4):
        with open(f'mlmo_t{fi}.c', 'w') as f:
            f.write('#include "stdint.h"\n')
            f.write('#include <ivy/xrt.h>\n')
            f.write('#include <ivy/sync.h>\n')
            f.write('#include <ivy/print.h>\n')
            f.write('#include <asm/barrier.h>\n')
            f.write('#include <linux/compiler.h>\n')
            while iter < end:
                test(iter, addr_space, f)
                iter+=1
            end = min(end+batch_size, test_times)

    with open('mlmo.c', 'w') as f:
        for i in range(test_times):
            f.write(f'void mlmo_test_{i}();\n')
        f.write('void mlmo_test(){\n')
        for i in range(test_times):
            f.write(f'mlmo_test_{i}();\n')
        f.write('}\n')


def test(iter: int, addr_space: purslane.addr_space.AddrSpace, f: io.TextIOWrapper):
    nr_cpus = ivy_app_cfg.NR_CPUS
    # 每个 cpu 分配 4 字节数据和 4 字节结果存储
    # allocate 4-bytes for data and 4-bytes final result for each cpu
    raddrs = []
    final_results = []
    for i in range(nr_cpus):
        raddrs.append(addr_space.AllocRandom(4, 4))
        final_results.append(addr_space.AllocRandom(4, 4))

    # 所有 cpu 4 个一组，分成若干组
    # divide cpus into groups, each of which consists of 4 cores
    cpus = [x for x in range(nr_cpus)]
    random.shuffle(cpus)

    raddrs_str = ','.join([f'(uint32_t*){ra: #x}' for ra in raddrs])
    final_results_str = ','.join(
        [f'(uint32_t*){fr: #x}' for fr in final_results])
    si_str = ','.join([f'{si}' for si in cpus])
    f.write(f'uint32_t* test_{iter}_raddrs[{nr_cpus}] = {{{raddrs_str}}};\n')
    f.write(
        f'uint32_t* test_{iter}_final_results[{nr_cpus}] = {{{final_results_str}}};\n')
    f.write(f'uint32_t test_{iter}_shuffle_idx[{nr_cpus}] = {{{si_str}}};\n')

    f.write(f'void mlmo_test_{iter}() {{\n')
    f.write('  unsigned long cid = xrt_get_core_id();\n')
    f.write(f'  unsigned long sid = test_{iter}_shuffle_idx[cid];\n')
    f.write('  unsigned long group_idx = sid / 4;\n')
    f.write('  unsigned long group_role = sid % 4;\n')
    f.write(f'  uint32_t* p_addr_0 = test_{iter}_raddrs[group_idx * 4];\n')
    f.write(f'  uint32_t* p_addr_1 = test_{iter}_raddrs[group_idx * 4 + 1];\n')
    f.write(
        f'  uint32_t* p_fr_0 = test_{iter}_final_results[group_idx * 4];\n')
    f.write(
        f'  uint32_t* p_fr_1 = test_{iter}_final_results[group_idx * 4 + 1];\n')
    f.write('  uint32_t k2_0=0, k2_1=0, k2_2=0;\n')
    f.write('  uint32_t k3_0=0, k3_1=0, k3_2=0;\n')
    f.write('  uint32_t fr_0=0;\n')
    f.write('  uint32_t fr_1=0;\n')
    f.write('\n')
    f.write(f'  WRITE_ONCE(*test_{iter}_raddrs[cid], 0);\n')
    f.write(f'  WRITE_ONCE(*test_{iter}_final_results[cid], 0);\n')
    f.write('\n')
    f.write('  cpu_barrier_wait();\n')
    f.write('\n')
    # P0, P1 write, P2, P3 read
    f.write('  switch (group_role) {\n')
    f.write('    case 0:\n')
    f.write('      smp_store_release(p_addr_0, 1);\n')
    f.write('      break;\n')
    f.write('\n')
    f.write('    case 1:\n')
    f.write('      smp_store_release(p_addr_1, 1);\n')
    f.write('      break;\n')
    f.write('\n')
    f.write('    case 2:\n')
    f.write('      k2_0 = smp_load_acquire(p_addr_0);\n')
    f.write('      k2_1 = smp_load_acquire(p_addr_1);\n')
    f.write('      k2_2 = k2_0 & (~k2_1);\n')
    f.write('      smp_store_release(p_fr_0, k2_2);\n')
    f.write('      break;\n')
    f.write('\n')
    f.write('    case 3:\n')
    f.write('      k3_0 = smp_load_acquire(p_addr_1);\n')
    f.write('      k3_1 = smp_load_acquire(p_addr_0);\n')
    f.write('      k3_2 = k3_0 & (~k3_1);\n')
    f.write('      smp_store_release(p_fr_1, k3_2);\n')
    f.write('      break;\n')
    f.write('\n')
    f.write('    default:\n')
    f.write('      break;\n')
    f.write('  }\n')
    f.write('\n')
    f.write('  cpu_barrier_wait();\n')
    f.write('\n')
    # checking in all cpus
    # verify that at least one of the final results is 0
    f.write('  fr_0 = smp_load_acquire(p_fr_0);\n')
    f.write('  fr_1 = smp_load_acquire(p_fr_1);\n')
    f.write('\n')
    f.write('  if (fr_0 && fr_1) {\n')
    f.write(f'    printf("error iter: {iter}, cid: %d, sid: %d\\n", cid, sid);\n')
    f.write('    printf("cid: %d, sid: %d, k2_0: %d, k2_1: %d, k2_2: %d, k3_0: %d, k3_1: %d, k3_2: %d\\n", cid, sid, k2_0, k2_1, k2_2, k3_0, k3_1, k3_2);\n')
    f.write('    xrt_exit(1);\n')
    f.write('  }\n')
    f.write('}\n')

    for r in raddrs:
        addr_space.Free(r, 4)
    for fr in final_results:
        addr_space.Free(fr, 4)


if __name__ == '__main__':
    main()
