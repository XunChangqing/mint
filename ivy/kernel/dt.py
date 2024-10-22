# author: zuoqian
# Copyright 2023. All rights reserved.

import pydevicetree
import typing
import dataclasses
from dataclasses import dataclass
from enum import Enum
import sys
import logging

logger = logging.getLogger('ivy.dt')


class PsciConduit(Enum):
    SMC = 1
    HVC = 2

# 备注，使用qemu时，如何生成dts文件
# ./qemu-system-aarch64 -machine virt,dumpdts=virt.dtb -cpu cortex-a76 -smp cpus=2
# dtc -I dtb -O dts virt.dtb >> virt.dts


@dataclass
class Memory:
    start: int
    size: int
    nid: int = 0


@dataclass
class Uart:
    name: str
    model: str
    base: int


@dataclass
class Cpu:
    id: int
    nid: int = 0


@dataclass
class Chosen:
    stdout_name: str = None
    stdout_addr: int = None
    console_baudrate: int = 115200


@dataclass
class PciRange:
    flags: int
    bus_addr: int
    cpu_addr: int
    size: int


@dataclass
class PciHost:
    name: str
    cfg_base: int
    cfg_size: int
    io_base: int = 0
    io_size: int = 0
    mem32_base: int = 0
    mem32_size: int = 0
    mem64_base: int = 0
    mem64_size: int = 0


@dataclass
class DeviceTree:
    memories: typing.List[Memory] = dataclasses.field(default_factory=list)
    memories_reserved: typing.List[Memory] = dataclasses.field(
        default_factory=list)
    uarts: typing.List[Uart] = dataclasses.field(default_factory=list)
    cpus: typing.List[Cpu] = dataclasses.field(default_factory=list)
    chosen: Chosen = None
    psci_conduit: PsciConduit = None
    pci_hosts: typing.List[PciHost] = dataclasses.field(default_factory=list)

# 解析dts文件，加载设备树信息


def device_populate_file(dts_file: str) -> DeviceTree:
    with open(dts_file, "r") as f:
        dts = f.read()
        return device_populate(dts)

# def simple_bus_device_populate(node: pydevicetree.Node, dt: DeviceTree):

# 根据dts文件解析得到device tree的python数据结构


def device_populate(dts: str) -> DeviceTree:
    ret_dt = DeviceTree()

    # 解析设备树源文件
    dt = pydevicetree.Devicetree.from_dts(dts)

    # 获取所有cpu节点
    # def cb_cpu(node: pydevicetree.Node):
    #     regs = node.get_reg()
    #     assert(len(regs) == 1)
    #     ret_dt.cpus.append(Cpu(regs[0][0]))

    # dt.filter(lambda node: node.name == 'cpu', cb_cpu)

    for node in dt.child_nodes():
        nt = node.get_field('device_type')
        if nt is None or nt != 'cpu':
            continue

        nid = node.get_field('numa-node-id')
        if nid is None:
            nid = 0

        regs = node.get_reg()
        assert (len(regs) == 1)
        print('cpu, id {:x} numa {:x}'.format(regs[0][0], nid))
        ret_dt.cpus.append(Cpu(regs[0][0], nid))

    # 获取所有可用存储空间
    for node in dt.child_nodes():
        nt = node.get_field('device_type')
        if nt is None or nt != 'memory':
            continue

        nid = node.get_field('numa-node-id')
        if nid is None:
            nid = 0

        sec_status = node.get_field('secure-status')
        if sec_status is not None:
            continue

        status = node.get_field('status')
        if status is not None and status == 'disabled':
            continue

        regs = node.get_reg()
        for reg in regs:
            print('memory 0x{:x} 0x{:x} 0x{:x}'.format(reg[0], reg[1], nid))
            ret_dt.memories.append(Memory(reg[0], reg[1], nid))

    # 根节点也作为simple bus处理
    # 暂时没有层次化处理，而是整个子树通过compatible匹配

    def cb_pci_host(node: pydevicetree.Node):
        regs = node.get_reg()
        assert (len(regs) == 1)
        reg = regs[0]
        logger.info(f'pci_host cfg base {reg[0]:#x}, size {reg[1]:#x}')
        pci_host = PciHost(
            name=node.name, cfg_base=reg[0], cfg_size=reg[1])

        ranges = node.get_ranges()
        for r in ranges:
            flags = r[0] >> 64
            bus_addr = r[0] & 0xFFFFFFFFFFFFFFFF
            cpu_addr = r[1]
            range_size = r[2]
            logger.info(
                f'range flags {flags:#x}, bus_addr {bus_addr:#x}, cpu_addr {cpu_addr:#x}, size {range_size:#x}')
            # pci_host.ranges.append(
            #     PciRange(flags=flags, bus_addr=bus_addr, cpu_addr=cpu_addr, size=range_size))
            mem_attr = (flags >> 24) & 0x3
            if mem_attr == 1:
                pci_host.io_base = cpu_addr
                pci_host.io_size = range_size
            elif mem_attr == 2:
                pci_host.mem32_base = cpu_addr
                pci_host.mem32_size = range_size
            elif mem_attr == 3:
                pci_host.mem64_base = cpu_addr
                pci_host.mem64_size = range_size
            else:
                logger.critical('illegal memory attribute')
                sys.exit(1)
        
        ret_dt.pci_hosts.append(pci_host)

    dt.match('pci-host-ecam-generic', cb_pci_host)

    # 获取pl011
    def cb_pl011(node: pydevicetree.Node):
        regs = node.get_reg()
        assert (len(regs) == 1)
        ret_dt.uarts.append(Uart(node.name, 'pl011', regs[0][0]))

    dt.match("arm,pl011", cb_pl011)

    # 获取dw16550
    def cb_dw16550(node: pydevicetree.Node):
        regs = node.get_reg()
        assert (len(regs) == 1)
        ret_dt.uarts.append(Uart(node.name, 'dw16550', regs[0][0]))

    # synopysis DesignWare DW_apb_uart 兼容16550协议
    dt.match('snps,dw-apb-uart', cb_dw16550)

    # 获取软仿模拟的uart
    def cb_simuart(node: pydevicetree.Node):
        regs = node.get_reg()
        assert (len(regs) == 1)
        ret_dt.uarts.append(Uart(node.name, 'dummy_uart', regs[0][0]))

    # synopysis DesignWare DW_apb_uart 兼容16550协议
    dt.match('ft,sim', cb_simuart)

    def cb_psci(node: pydevicetree.Node):
        method = node.get_field('method')
        if method == 'smc':
            ret_dt.psci_conduit = PsciConduit.SMC
        elif method == 'hvc':
            ret_dt.psci_conduit = PsciConduit.HVC
        else:
            logger.warning('psci method does not exist, default to smc')
            ret_dt.psci_conduit = PsciConduit.SMC
            # raise Exception('unsupported psci method')
        print('psci method ', method)

    dt.match('.*arm,psci-0\.2.*', cb_psci)

    if ret_dt.psci_conduit is None:
        logger.warning('the psci node does not exist, use SMC by default')
        ret_dt.psci_conduit = PsciConduit.SMC

    # 获取chosen
    chosen_node = dt.get_by_path('/chosen')
    if chosen_node is not None:
        ret_dt.chosen = Chosen()
        chosen_stdout_path = chosen_node.get_field('stdout-path')
        if chosen_stdout_path is not None:
            stdout_node = dt.get_by_path(chosen_stdout_path)
            ret_dt.chosen.stdout_name = stdout_node.name
            ret_dt.chosen.stdout_addr = stdout_node.address
        # boot args
        bootargs = chosen_node.get_field('bootargs')
        # bootargs = "console=ttyS0,921600 earlycon=uart8250,mmio32,0x28001000 root=/dev/ram0 rw";
        if bootargs:
            args_list = bootargs.split()
            for arg in args_list:
                argkv = arg.split('=')
                if argkv[0] == 'console':
                    values = argkv[1].split(',')
                    ret_dt.chosen.console_baudrate = int(values[1])

    return ret_dt
