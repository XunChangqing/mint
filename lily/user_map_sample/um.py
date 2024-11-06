import ivy_app_cfg
import ivy.kernel.dt
import ivy.kernel.pt
import ivy.cmd.app
import purslane.addr_space

def main():
    addr_space = purslane.addr_space.AddrSpace()
    for mr in ivy_app_cfg.free_mem_ranges:
        addr_space.AddNode(mr.base, mr.size, mr.numa_id)
    # device_tree = ivy.kernel.dt.device_populate_file(ivy_app_cfg.device_tree_file)
 
    user_pt = ivy.kernel.pt.UserPageTable(ivy_app_cfg.PAGE_SIZE)

    pa = addr_space.Alloc(64*1024, 64)
    va = ivy.kernel.pt.UVA_START
    # user_pt.map_range(pa, va, 64*1024, ivy.kernel.pt.PROT_NORMAL)
    user_pt.map_range(pa, va, 64*1024, ivy.kernel.pt.PROT_DEVICE_nGnRnE)
    user_pt.dumpf('user_pt.S')

    with open('user_map.h', 'w') as f:
        f.write('#pragma once\n')
        f.write(f'#define USER_ADDR ({va}ULL)\n')
    
if __name__ == '__main__':
    main()
