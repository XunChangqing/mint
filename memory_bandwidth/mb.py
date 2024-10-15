import ivy_app_cfg
import purslane
from purslane.addr_space import AddrSpace
import logging
from dataclasses import dataclass
import typing
import ivy.cfg

logger = logging.getLogger('memory_bandwidth')


@dataclass
class Job:
    size: int = 0
    src: int = 0
    dst: int = 0
    cpu_mask: bool = False

    def format(self) -> str:
        if self.cpu_mask:
            return f'{{.size = {self.size: #x}, .src = (void*){self.src:#x}, .dst = (void*){self.dst:#x}, .cpu_mask = true }}'
        else:
            return f'{{.size = 0, .src = NULL, .dst = NULL, .cpu_mask = false }}'


@dataclass
class ChipJob:
    name: str
    cpu_jobs: list[Job]

    def format(self) -> str:
        cpu_jobs_str = ', '.join([jj.format() for jj in self.cpu_jobs])
        return f'{{.name = "{self.name}", .cpu_jobs = {{ {cpu_jobs_str} }} }}'


def bw_peak(cpus: typing.List[ivy.cfg.Cpu], addr_space: AddrSpace) -> ChipJob:
    buf_size = 64*1024*1024
    addr_list = []
    cj = ChipJob(name='peak memory-copy bandwidth test, each cpu accesses the local memory, both source and destination memories size are 64MB ', cpu_jobs=[])
    for cpu in cpus:
        cpu_mem = addr_space.AllocNid(buf_size*2, 64, cpu.numa_id)
        src = cpu_mem
        dst = src + buf_size
        addr_list.append(cpu_mem)
        cj.cpu_jobs.append(Job(size=buf_size, src=src, dst=dst, cpu_mask=True))

    for addr in addr_list:
        addr_space.Free(addr)

    return cj


def bw_cross_numa(cpus: typing.List[ivy.cfg.Cpu], addr_space: AddrSpace, mem_numa: int, cpu_from) -> ChipJob:
    """create bandwidth test job across numa

    Parameters
    ----------------
    mem_numa: the numa id of the target memory
    cpu_from: dict{int:int}, {0:2, 1:2} means 2 cpus from numa 0, and 2 cpus from numa 1

    Returns
    ----------------
    the job
    """
    buf_size = 64*1024*1024

    cpu_from_str = ','.join(
        [f'{cfv} cpus from numa {cfk}' for cfk, cfv in cpu_from.items()])
    cj = ChipJob(
        name=f'bw cross numa, the numa id of the memory {mem_numa}, {cpu_from_str}', cpu_jobs=[])

    addr_list = []

    for cpu in cpus:
        if cpu.numa_id in cpu_from and cpu_from[cpu.numa_id] > 0:
            cpu_from[cpu.numa_id] -= 1
            cpu_mem = addr_space.AllocNid(buf_size*2, 64, mem_numa)
            addr_list.append(cpu_mem)
            src = cpu_mem
            dst = cpu_mem+buf_size
            cj.cpu_jobs.append(
                Job(size=buf_size, src=src, dst=dst, cpu_mask=True))
        else:
            cj.cpu_jobs.append(Job())

    for addr in addr_list:
        addr_space.Free(addr)

    return cj


def main():
    logging.basicConfig(level=logging.INFO)
    logger.info('mb main')
    addr_space = purslane.addr_space.AddrSpace()
    for fr in ivy_app_cfg.free_mem_ranges:
        logger.info(
            f'addr space region: {fr.base:#x}, {fr.size:#x}, {fr.numa_id}')
        addr_space.AddNode(fr.base, fr.size, fr.numa_id)

    cpus = ivy_app_cfg.cpus
    cjs = []
    cjs.append(bw_peak(cpus, addr_space))
    cjs.append(bw_cross_numa(cpus, addr_space, 0, {0: 2}))

    cjs.append(bw_cross_numa(cpus, addr_space, 2, {0: 2, 1: 2}))
    cjs.append(bw_cross_numa(cpus, addr_space, 2, {0: 4, 1: 4}))
    cjs.append(bw_cross_numa(cpus, addr_space, 2, {0: 8, 1: 8}))

    with open('mb.h', 'w') as f:
        f.write('struct chip_job job_list[]={\n')

        for cj in cjs:
            if cj is not None:
                f.write(f'{cj.format()}')
                f.write(',\n')
        # end of the job list
        f.write('};\n')


if __name__ == '__main__':
    main()
