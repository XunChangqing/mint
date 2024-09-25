# Copyright (C) 2024 zuoqian

import argparse
import typing
from dataclasses import dataclass
import importlib.util
from pathlib import Path

from ivy.kernel import dt
from ivy.kernel import mb
from ivy.kernel import pt
from ivy.kernel import cfg

from ivy.cfg import Config

SIZE_KB = 1024
SIZE_64KB = 64*SIZE_KB
SIZE_16KB = 16*SIZE_KB
SIZE_4KB = 4*SIZE_KB
SIZE_MB = 1024*SIZE_KB
SIZE_GB = 1024*SIZE_MB

TEXT_OFFSET = 0x80000

# 计算核栈尺寸常量
CORE_STACK_SIZE = 128*SIZE_KB
MAX_TEXT_SIZE = 64*SIZE_MB

PAGE_SIZE_MACRO_DICT = {
  SIZE_64KB: "IVY_CFG_ARM64_64K_PAGES",
  SIZE_16KB: "IVY_CFG_ARM64_16K_PAGES",
  SIZE_4KB: "IVY_CFG_ARM64_4K_PAGES"
}

PAGE_SHIFT_DICT = {
  SIZE_64KB: 16,
  SIZE_16KB: 14,
  SIZE_4KB: 12
}

# uarts
class PL011:
  def __init__(self):
    self._base = 0

  @property
  def base(self):
    return self._base

  @base.setter
  def base(self, v):
    self._base = v

  def dump_def(self, f):
    f.write('#define IVY_DT_STDOUT_PL011\n')
    f.write('#define IVY_DT_STDOUT_PL011_BASE (0x{:x})\n'.format(self._base))

class DW16550:
  def __init__(self):
      self._base = 0

  @property
  def base(self):
    return self._base

  @base.setter
  def base(self, v):
    self._base = v

  def dump_def(self, f):
    f.write('#define DT_STDOUT_DW16550\n')
    f.write('#define DT_STDOUT_DW16550_BASE (0x{:x})\n'.format(self._base))

class DummyUart:
  def __init__(self):
    self._base = 0

  @property
  def base(self):
    return self._base

  @base.setter
  def base(self, v):
    self._base = v

  def dump_def(self, f):
    f.write('#define DT_STDOUT_DUMMY\n')
    f.write('#define DT_STDOUT_DUMMY_BASE (0x{:x})\n'.format(self._base))

UARTS_DRIVER_DICT = {
  "pl011": PL011,
  "dw16550": DW16550,
  "dummy_uart": DummyUart
}

# 支持静态生成的运行时系统
class App:
  def __init__(self, dt: dt.DeviceTree, cfg : Config):
    self._dt = dt
    self._cfg = cfg
    # 额外增加的数据段
    self._data_secs = []
    # 额外增加的include路径
    self._incs = []
    # 额外增加的源码文件
    self._srcs = []
    self._asms = []

    # 所有分配地址的表，以起始地址检索，在free时，只需要提供地址即可
    self._alloc_dict = {}
    # 决定页表尺寸，并建立线性映射页表
    page_size_opts = [SIZE_4KB, SIZE_16KB, SIZE_64KB]
    page_size = SIZE_64KB
    if cfg and cfg.page_size:
      if cfg.page_size not in page_size_opts:
        raise Exception("the page size is illegal")
      page_size = cfg.page_size

    self._page_size = page_size

    ptg_cfg = pt.Config()
    if page_size == SIZE_64KB:
        ptg_cfg.page_shift = 16
    elif page_size == SIZE_16KB:
        ptg_cfg.page_shift = 14
    else:
        ptg_cfg.page_shift = 12

    lpt = pt.PageTableGen(ptg_cfg)
    hpt = pt.PageTableGen(ptg_cfg)
    self._lpt = lpt
    self._hpt = hpt

    # 记载所有存储段
    self._mb = mb.MemBlock()

    linear_mapping_flag = 0
    if cfg:
      linear_mapping_flag = cfg.linear_mapping_flag
    for mr in dt.memories:
      self._mb.AddNode(mr.start, mr.size, mr.nid)
      # 所有可用存储空间全部线性映射为cacheable、可执行，可读写
      lpt.MapRange(mr.start, mr.start, mr.size,
                    pt.PAGE_KERNEL_EXEC, linear_mapping_flag)

    # reserve部分也映射了，但是不会使用
    for mr in dt.memories_reserved:
      self._mb.Reserve(mr.start, mr.size)

    # 决定代码段起始位置，并分配代码段存储，起始位置对齐到page_size
    if not cfg or not cfg.load_addr:
      # 没有则从ram地址最低处 + TEXT_OFFSET 开始
      text_base = self._mb.AllocRange(MAX_TEXT_SIZE, page_size,
                                        self._mb.FreeLowAddr() + TEXT_OFFSET, None)
    else:
      # TOFIX
      # 需要确保 cfg.load_addr 对齐到page size，否则会失败失败
      # 分配指定位置存储，确保该片地址可用
      text_base = self._mb.AllocRange(MAX_TEXT_SIZE, page_size,
                          cfg.load_addr, None)

    self._text_base = text_base

    print("text base: {:x}".format(text_base))

    # 决定活跃处理核，总是所有核都运行
    self._active_cores = dt.cpus

    # 将所有串口映射到线性地址空间，便于访问
    for uart in dt.uarts:
      lpt.MapRange(uart.base, uart.base, page_size,
                    pt.PROT_DEVICE_nGnRnE)

    # 决定标准输出所使用串口的名字和base
    # 如果有配置，则使用配置项
    if dt.chosen and dt.chosen.stdout_name:
      stdout_name = dt.chosen.stdout_name
      stdout_addr = dt.chosen.stdout_addr
      # 确认该uart存在
      found = False
      for uart in dt.uarts:
        if uart.name == stdout_name and uart.base == stdout_addr:
          found = True
          stdout_model = uart.model
      if not found:
        raise Exception("stdout not exist")
    # 否则寻找第一个可以支持的串口
    else:
      for uart in dt.uarts:
        if uart.model in UARTS_DRIVER_DICT:
          stdout_name = uart.name
          stdout_model = uart.model
          stdout_addr = uart.base
          break

    if dt.chosen:
      self._stdout_baudrate = dt.chosen.console_baudrate
    else:
      self._stdout_baudrate = 115200

    # 根据标准输出所使用的串口，加载对应驱动
    stdout_drv = UARTS_DRIVER_DICT[stdout_model]()
    stdout_drv.base = stdout_addr
    print('uart: {}@{:x} baudrate {}'.format(stdout_name, stdout_drv.base, self._stdout_baudrate))

    self._stdout_drv = stdout_drv

  # 将指定物理地址映射到指定虚拟地址上，比如是高位地址，配置到ttbr1
  # 0xFFFF000000000000开始，允许以激励所需的存储属性访问该物理地址
  # 范围，比如可以支持以device模式访问特定存储范围，也可以重新映射io设备

  @property
  def page_size(self):
    return self._page_size

  @property
  def text_base(self):
    return self._text_base

  @property
  def text_end(self):
    return self._text_base+MAX_TEXT_SIZE

  # 存储分配，返回地址
  def Alloc(self, size, align):
    addr = self._mb.Alloc(size, align)
    self._alloc_dict[addr] = size
    return addr

  # 释放分配的存储
  def Free(self, addr):
    size = self._alloc_dict[addr]
    self._mb.Free(addr, size)

  # 获取所有空闲的存储段
  def FreeRanges(self):
    return self._mb.FreeRanges()

  # 获取活跃处理核数量
  @property
  def nr_cpus(self):
    return len(self._active_cores)

  # 不允许在任意位置添加 loadable section
  # 添加一个数据段，用户必须确保该片地址经过分配得到
  # 并且必须保证放在该section的内容不会超过存储尺寸限制
  # rt会自动生成一个obj文件
  # def AddDataSection(self, name, addr, buf):
  #     self._data_secs.append(Section(name, addr, buf))

  # 生成代码文件，在当前目录下建立
  # 配置宏定义 xfg_gen.h
  # 页表内容文件 xpt.S
  # 运行时头文件 xrt.h
  # 运行时源文件 xrt.c
  # xpt.S, xcfg_gen.h, xrt.h, xrt.c
  def Gen(self):
    self.__GenDT()
    self.__GenCfg()
    self.__GenPageTable()

  def __GenDT(self):
    with open('ivy_dt.h', 'w') as f:
      f.write('#pragma once\n')

      f.write("#define IVY_DT_NR_CPUS ({})\n".format(
        len(self._active_cores)))
      f.write("\n")

      self._stdout_drv.dump_def(f)
      f.write(f'#define IVT_DT_UART_BARD_RATE ({self._stdout_baudrate})\n')

      if self.nr_cpus > 1:
        if self._dt.psci_conduit == dt.PsciConduit.SMC:
          f.write('#define IVY_DT_PSCI_CONDUIT_SMC\n')
        elif self._dt.psci_conduit == dt.PsciConduit.HVC:
          f.write('#define DT_PSCI_CONDUIT_HVC\n')
        else:
          raise Exception('psci conduit is None')
          
      f.write(f'#define IVY_DT_NUM_MEMORY {len(self._dt.memories)}\n')
      f.write(f'#define IVY_DT_NUM_RESERVED_MEMORY {len(self._dt.memories_reserved)}\n')
      f.write(f'#define IVY_DT_NUM_FREE_MEMORY {len(list(self.FreeRanges()))}\n')

      f.write(
        '''
        #ifndef __ASSEMBLY__
        #ifndef __LINKAGE__
        #include <stdint.h>
        // 设备树中 cpu id 信息
        extern uint64_t ivy_dt_cpu_id_map[IVY_DT_NR_CPUS];

        // 设备数中 cpu 信息
        typedef struct dt_cpu {
          uint64_t id;
          uint64_t numa_id;
        } dt_cpu_t;
        extern dt_cpu_t ivy_dt_cpus[IVY_DT_NR_CPUS];

        // 设备树中存储信息
        typedef struct dt_memory {
          uint64_t start;
          uint64_t size;
          uint64_t numa_id;
        } dt_memory_t;

        extern dt_memory_t ivy_dt_memories[IVY_DT_NUM_MEMORY];
        extern dt_memory_t ivy_dt_reserved_memories[IVY_DT_NUM_RESERVED_MEMORY];
        extern dt_memory_t ivy_dt_free_memories[IVY_DT_NUM_FREE_MEMORY];

        #endif
        #endif
        '''
        )

    with open('ivy_dt.c', 'w') as f:
      f.write('#include "ivy_dt.h"\n')
      # mpidr bit31 为 res1，即总是为1
      cid_str = ["{:#x}".format(cid.id) for cid in self._active_cores]
      # print(", ".join(cid_str))
      f.write("uint64_t ivy_dt_cpu_id_map[{0}] = {{{1}}};\n".format(
        self.nr_cpus, ", ".join(cid_str)))
      
      f.write('dt_cpu_t ivy_dt_cpus[IVY_DT_NR_CPUS] = {\n')
      for cpu in self._dt.cpus:
        f.write(f'{{.id = 0x{cpu.id:x}, .numa_id = 0x{cpu.nid:x}}},\n')
      f.write('};\n')
      
      f.write('dt_memory_t ivy_dt_memories[IVY_DT_NUM_MEMORY] = {\n')
      for mem in self._dt.memories:
        f.write('{{.start = 0x{:x}, .size = 0x{:x}, .numa_id = 0x{:x}}},\n'.format(mem.start, mem.size, mem.nid))
      f.write('};\n')

      f.write('dt_memory_t ivy_dt_reserved_memories[IVY_DT_NUM_RESERVED_MEMORY] = {\n')
      for mem in self._dt.memories_reserved:
        f.write('{{.start = 0x{:x}, .size = 0x{:x}, .numa_id = 0x{:x}}},\n'.format(mem.start, mem.size, mem.nid))
      f.write('};\n')

      f.write('dt_memory_t ivy_dt_free_memories[IVY_DT_NUM_FREE_MEMORY] = {\n')
      for start, end, nid in self.FreeRanges():
        f.write('{{.start = 0x{:x}, .size = 0x{:x}, .numa_id = 0x{:x}}},\n'.format(start, end-start, nid))
      f.write('};\n')

  def __GenCfg(self):
    with open("ivy_cfg.h", "w") as f:
      f.write("#define IVY_CFG_TEXT_BASE ({:#x})\n".format(self._text_base))
      f.write("#define IVY_CFG_TEXT_OFFSET ({:#x})\n".format(TEXT_OFFSET))
      f.write("#define IVY_CFG_TEXT_END ({:#x})\n".format(self.text_end))
      f.write("\n")

      f.write("#define {}\n".format(
          PAGE_SIZE_MACRO_DICT[self._page_size]))
      f.write("#define IVY_CFG_PAGE_SHIFT ({})\n".format(
          PAGE_SHIFT_DICT[self._page_size]))
      f.write("#define IVY_CFG_PAGE_SIZE ({})\n".format(self._page_size))
      f.write("#define IVY_CFG_CORE_STACK_SIZE ({:#x})\n".format(
          CORE_STACK_SIZE))
      
      if self._cfg and self._cfg.no_booter:
        f.write('#define IVY_CFG_NO_BOOTER\n')

  def __GenPageTable(self):
    # 与页表内容配套的寄存器配置值
    with open('ivy_pt.h', 'w') as f:
      f.write('#pragma once\n')
      f.write("#define MAIR_EL1_VAL ({:#x})\n".format(self._lpt.mair_el1_val))
      f.write("#define TCR_EL1_VAL ({:#x})\n".format(self._lpt.tcr_el1_val))
      f.write("#define SCTLR_EL1_VAL ({:#x})\n".format(
          self._lpt.sctlr_el1_val))
      f.write("\n")
    # 页表内容
    self._lpt.DumpToFile("ivy_pt.S")

def ImportModuleByPath(mod_path):
  spec = importlib.util.spec_from_file_location('my_module', mod_path)
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return module

def Main():
  parser = argparse.ArgumentParser()
  parser.add_argument("--device_tree", help="device tree source file", type=str, required=True)
  parser.add_argument("--cfg", help="config", type=str)
  args = parser.parse_args()

  dev_tree = dt.device_populate_file(args.device_tree)

  cfg_path = Path(args.cfg)
  cfg_path = cfg_path.absolute().resolve()
  cfg_mod = ImportModuleByPath(cfg_path)

  cfg = cfg_mod.ivy_cfg
  print(cfg)

  app = App(dev_tree, cfg)
  # 输出 c 语言接口
  app.Gen()

  # 输出 pss 接口
  # with open('ivy_app_cfg.pss', 'w') as f:
  #   f.write('package ivy_app_cfg{\n')
  #   f.write(f'const bit[32] NUM_CPUS = {app.nr_cpus};\n')
  #   f.write('}\n')

  # 输出 python 输出
  with open('ivy_app_cfg.py', 'w') as f:
    f.write(f'TEXT_BASE = {app.text_base:#x}\n')
    f.write(f'NR_CPUS = {app.nr_cpus}\n')
    f.write(f'PAGE_SIZE = {app.page_size:#x}\n')
    f.write(f'MAX_TEXT_SIZE = {MAX_TEXT_SIZE:#x}\n')
    # 输出空闲存储空间数组
    f.write(f'FREE_RANGES = [')
    for fr in app.FreeRanges():
      f.write(f'({fr[0]:#x}, {fr[1]:#x}, {fr[2]:#x}),')
    f.write(']\n')

