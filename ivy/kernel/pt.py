from enum import Enum
from enum import IntFlag
from dataclasses import dataclass
import sys
import logging

logger = logging.getLogger('ivy.kernel.pt')

CONFIG_CPU_BIG_ENDIAN = False

PHY_ADDR_MASK = 0xFFFFFFFFFFFFFFFF
BIT64_MASK = 0xFFFFFFFFFFFFFFFF

# ref arch/arm64/include/asm/sysreg.h
# Common SCTLR_ELx flags.
SCTLR_ELx_EE = (1 << 25)
SCTLR_ELx_IESB = (1 << 21)
SCTLR_ELx_WXN = (1 << 19)
SCTLR_ELx_I = (1 << 12)
SCTLR_ELx_SA = (1 << 3)
SCTLR_ELx_C = (1 << 2)
SCTLR_ELx_A = (1 << 1)
SCTLR_ELx_M = 1

#  SCTLR_EL1 specific flags.
SCTLR_EL1_UCI = (1 << 26)
SCTLR_EL1_E0E = (1 << 24)
SCTLR_EL1_SPAN = (1 << 23)
SCTLR_EL1_NTWE = (1 << 18)
SCTLR_EL1_NTWI = (1 << 16)
SCTLR_EL1_UCT = (1 << 15)
SCTLR_EL1_DZE = (1 << 14)
SCTLR_EL1_UMA = (1 << 9)
SCTLR_EL1_SED = (1 << 8)
SCTLR_EL1_ITD = (1 << 7)
SCTLR_EL1_CP15BEN = (1 << 5)
SCTLR_EL1_SA0 = (1 << 4)

SCTLR_EL1_RES1 = ((1 << 11) | (1 << 20) | (1 << 22) | (1 << 28) | (1 << 29))
SCTLR_EL1_RES0 = ((1 << 6) | (1 << 10) | (1 << 13) | (1 << 17) |
                  (1 << 27) | (1 << 30) | (1 << 31) |
                  (0xffffffff << 32))

if CONFIG_CPU_BIG_ENDIAN:
    ENDIAN_SET_EL1 = (SCTLR_EL1_E0E | SCTLR_ELx_EE)
    ENDIAN_CLEAR_EL1 = 0
else:
    ENDIAN_SET_EL1 = 0
    ENDIAN_CLEAR_EL1 = (SCTLR_EL1_E0E | SCTLR_ELx_EE)

MT_DEVICE_nGnRnE = 0
MT_DEVICE_nGnRE = 1
MT_DEVICE_GRE = 2
MT_NORMAL_NC = 3
MT_NORMAL = 4
MT_NORMAL_WT = 5

# 程序中mair_el1配置
# define MAIR(attr, mt)	((attr) << ((mt) * 8))
# 	/*
# 	 * Memory region attributes for LPAE:
# 	 *
# 	 *   n = AttrIndx[2:0]
# 	 *			n	MAIR
# 	 *   DEVICE_nGnRnE	000	00000000
# 	 *   DEVICE_nGnRE	001	00000100
# 	 *   DEVICE_GRE		010	00001100
# 	 *   NORMAL_NC		011	01000100
# 	 *   NORMAL		100	11111111
# 	 *   NORMAL_WT		101	10111011
# 	 */
# 	ldr	x5, =MAIR(0x00, MT_DEVICE_nGnRnE) | \
# 		     MAIR(0x04, MT_DEVICE_nGnRE) | \
# 		     MAIR(0x0c, MT_DEVICE_GRE) | \
# 		     MAIR(0x44, MT_NORMAL_NC) | \
# 		     MAIR(0xff, MT_NORMAL) | \
# 		     MAIR(0xbb, MT_NORMAL_WT)
# 	msr	mair_el1, x5
def MAIR(attr, mt):
    return (attr << ((mt)*8))

# ref arch/arm64/include/asm/pgtable-hwdef.h
def ARM64_HW_PGTABLE_LEVELS(va_bits, page_shift):
    return (((va_bits) - 4) // (page_shift - 3))

def ARM64_HW_PGTABLE_LEVEL_SHIFT(n, page_shift):
    return ((page_shift - 3) * (4 - (n)) + 3)


# hardware page table definitions
# level 1 descriptor (PUD)
PUD_TYPE_TABLE = (3 << 0)
PUD_TYPE_BIT = (1 << 1)
PUD_TYPE_MASK = (3 << 0)
PUD_TYPE_SECT = (1 << 0)

# level 2 descriptor (PMD)
PMD_TYPE_MASK = (3 << 0)
PMD_TYPE_FAULT = (0 << 0)
PMD_TYPE_TABLE = (3 << 0)
PMD_TYPE_SECT = (1 << 0)
PMD_TABLE_BIT = (1 << 1)

# section
PMD_SECT_VALID = (1 << 0)
PMD_SECT_USER = (1 << 6)  # AP[1]
PMD_SECT_RDONLY = (1 << 7)  # AP[2]
PMD_SECT_S = (3 << 8)
PMD_SECT_AF = (1 << 10)
PMD_SECT_NG = (1 << 11)
PMD_SECT_CONT = (1 << 52)
PMD_SECT_PXN = (1 << 53)
PMD_SECT_UXN = (1 << 54)

# AttrIndx[2:0] encoding (mapping attributes defined in the MAIR registers)
def PMD_ATTRINDX(t):
    return t << 2

PMD_ATTRINDX_MASK = (7 << 2)

# level 3 descriptor (PTE)
PTE_TYPE_MASK = (3 << 0)
PTE_TYPE_FAULT = (0 << 0)
PTE_TYPE_PAGE = (3 << 0)
PTE_TABLE_BIT = (1 << 1)
PTE_USER = (1 << 6)
PTE_RDONLY = (1 << 7)
PTE_SHARED = (3 << 8)
PTE_AF = (1 << 10)
PTE_NG = (1 << 11)
PTE_DBM = (1 << 51)
PTE_CONT = (1 << 52)
PTE_PXN = (1 << 53)
PTE_UXN = (1 << 54)
PTE_HYP_XN = (1 << 54)

# AttrIndx[2:0] encoding (mapping attributes defined in the MAIR registers)
def PTE_ATTRINDX(t):
    return t << 2


PTE_ATTRINDX_MASK = (7 << 2)

# TCR flags
TCR_T0SZ_OFFSET = 0
TCR_T1SZ_OFFSET = 16


def TCR_T0SZ(x):
    return (64 - x) << TCR_T0SZ_OFFSET


def TCR_T1SZ(x):
    return (64 - x) << TCR_T1SZ_OFFSET


def TCR_TxSZ(x):
    return TCR_T0SZ(x) | TCR_T1SZ(x)


TCR_TxSZ_WIDTH = 6
TCR_T0SZ_MASK = ((1 << TCR_TxSZ_WIDTH) - 1) << TCR_T0SZ_OFFSET

TCR_IRGN0_SHIFT = 8
TCR_IRGN0_MASK = (3 << TCR_IRGN0_SHIFT)
TCR_IRGN0_NC = (0 << TCR_IRGN0_SHIFT)
TCR_IRGN0_WBWA = (1 << TCR_IRGN0_SHIFT)
TCR_IRGN0_WT = (2 << TCR_IRGN0_SHIFT)
TCR_IRGN0_WBnWA = (3 << TCR_IRGN0_SHIFT)

TCR_IRGN1_SHIFT = 24
TCR_IRGN1_MASK = (3 << TCR_IRGN1_SHIFT)
TCR_IRGN1_NC = (0 << TCR_IRGN1_SHIFT)
TCR_IRGN1_WBWA = (1 << TCR_IRGN1_SHIFT)
TCR_IRGN1_WT = (2 << TCR_IRGN1_SHIFT)
TCR_IRGN1_WBnWA = (3 << TCR_IRGN1_SHIFT)

TCR_IRGN_NC = (TCR_IRGN0_NC | TCR_IRGN1_NC)
TCR_IRGN_WBWA = (TCR_IRGN0_WBWA | TCR_IRGN1_WBWA)
TCR_IRGN_WT = (TCR_IRGN0_WT | TCR_IRGN1_WT)
TCR_IRGN_WBnWA = (TCR_IRGN0_WBnWA | TCR_IRGN1_WBnWA)
TCR_IRGN_MASK = (TCR_IRGN0_MASK | TCR_IRGN1_MASK)

TCR_ORGN0_SHIFT = 10
TCR_ORGN0_MASK = (3 << TCR_ORGN0_SHIFT)
TCR_ORGN0_NC = (0 << TCR_ORGN0_SHIFT)
TCR_ORGN0_WBWA = (1 << TCR_ORGN0_SHIFT)
TCR_ORGN0_WT = (2 << TCR_ORGN0_SHIFT)
TCR_ORGN0_WBnWA = (3 << TCR_ORGN0_SHIFT)

TCR_ORGN1_SHIFT = 26
TCR_ORGN1_MASK = (3 << TCR_ORGN1_SHIFT)
TCR_ORGN1_NC = (0 << TCR_ORGN1_SHIFT)
TCR_ORGN1_WBWA = (1 << TCR_ORGN1_SHIFT)
TCR_ORGN1_WT = (2 << TCR_ORGN1_SHIFT)
TCR_ORGN1_WBnWA = (3 << TCR_ORGN1_SHIFT)

TCR_ORGN_NC = (TCR_ORGN0_NC | TCR_ORGN1_NC)
TCR_ORGN_WBWA = (TCR_ORGN0_WBWA | TCR_ORGN1_WBWA)
TCR_ORGN_WT = (TCR_ORGN0_WT | TCR_ORGN1_WT)
TCR_ORGN_WBnWA = (TCR_ORGN0_WBnWA | TCR_ORGN1_WBnWA)
TCR_ORGN_MASK = (TCR_ORGN0_MASK | TCR_ORGN1_MASK)

TCR_SH0_SHIFT = 12
TCR_SH0_MASK = (3 << TCR_SH0_SHIFT)
TCR_SH0_INNER = (3 << TCR_SH0_SHIFT)

TCR_SH1_SHIFT = 28
TCR_SH1_MASK = (3 << TCR_SH1_SHIFT)
TCR_SH1_INNER = (3 << TCR_SH1_SHIFT)
TCR_SHARED = (TCR_SH0_INNER | TCR_SH1_INNER)

TCR_TG0_SHIFT = 14
TCR_TG0_MASK = (3 << TCR_TG0_SHIFT)
TCR_TG0_4K = (0 << TCR_TG0_SHIFT)
TCR_TG0_64K = (1 << TCR_TG0_SHIFT)
TCR_TG0_16K = (2 << TCR_TG0_SHIFT)

TCR_TG1_SHIFT = 30
TCR_TG1_MASK = (3 << TCR_TG1_SHIFT)
TCR_TG1_16K = (1 << TCR_TG1_SHIFT)
TCR_TG1_4K = (2 << TCR_TG1_SHIFT)
TCR_TG1_64K = (3 << TCR_TG1_SHIFT)

TCR_IPS_SHIFT = 32
TCR_IPS_MASK = (7 << TCR_IPS_SHIFT)
TCR_A1 = (1 << 22)
TCR_ASID16 = (1 << 36)
TCR_TBI0 = (1 << 37)
TCR_HA = (1 << 39)
TCR_HD = (1 << 40)
TCR_NFD1 = (1 << 54)

# ref arch/arm64/include/asm/pgtable-prot.h
PTE_VALID = (1 << 0)
PTE_WRITE = PTE_DBM
PTE_DIRTY = (1 << 55)
PTE_SPECIAL = (1 << 56)
PTE_PROT_NONE = (1 << 58)

_PROT_DEFAULT = (PTE_TYPE_PAGE | PTE_AF | PTE_SHARED)
_PROT_SECT_DEFAULT = (PMD_TYPE_SECT | PMD_SECT_AF | PMD_SECT_S)

PROT_DEFAULT = (_PROT_DEFAULT)
PROT_SECT_DEFAULT = (_PROT_SECT_DEFAULT)

PROT_DEVICE_nGnRnE = (PROT_DEFAULT | PTE_PXN | PTE_UXN |
                      PTE_WRITE | PTE_ATTRINDX(MT_DEVICE_nGnRnE))
PROT_DEVICE_nGnRE = (PROT_DEFAULT | PTE_PXN | PTE_UXN |
                     PTE_WRITE | PTE_ATTRINDX(MT_DEVICE_nGnRE))
PROT_NORMAL_NC = (PROT_DEFAULT | PTE_PXN | PTE_UXN |
                  PTE_WRITE | PTE_ATTRINDX(MT_NORMAL_NC))
PROT_NORMAL_WT = (PROT_DEFAULT | PTE_PXN | PTE_UXN |
                  PTE_WRITE | PTE_ATTRINDX(MT_NORMAL_WT))
PROT_NORMAL = (PROT_DEFAULT | PTE_PXN | PTE_UXN |
               PTE_WRITE | PTE_ATTRINDX(MT_NORMAL))

PROT_SECT_DEVICE_nGnRE = (PROT_SECT_DEFAULT | PMD_SECT_PXN |
                          PMD_SECT_UXN | PMD_ATTRINDX(MT_DEVICE_nGnRE))
PROT_SECT_NORMAL = (PROT_SECT_DEFAULT | PMD_SECT_PXN |
                    PMD_SECT_UXN | PMD_ATTRINDX(MT_NORMAL))
PROT_SECT_NORMAL_EXEC = (
    PROT_SECT_DEFAULT | PMD_SECT_UXN | PMD_ATTRINDX(MT_NORMAL))

_PAGE_DEFAULT = (_PROT_DEFAULT | PTE_ATTRINDX(MT_NORMAL))

# kernel
# 特权态可读写，特权用户态都不可执行
PAGE_KERNEL = (PROT_NORMAL)
PAGE_KERNEL_RO = ((PROT_NORMAL & ~PTE_WRITE) | PTE_RDONLY)
PAGE_KERNEL_ROX = ((PROT_NORMAL & ~(PTE_WRITE | PTE_PXN)) | PTE_RDONLY)
# 特权态可执行
PAGE_KERNEL_EXEC = (PROT_NORMAL & ~PTE_PXN)
PAGE_KERNEL_EXEC_CONT = ((PROT_NORMAL & ~PTE_PXN) | PTE_CONT)

PAGE_NONE = (((_PAGE_DEFAULT) & ~PTE_VALID) | PTE_PROT_NONE |
             PTE_RDONLY | PTE_NG | PTE_PXN | PTE_UXN)
# shared+writable pages are clean by default, hence PTE_RDONLY|PTE_WRITE
# user
PAGE_SHARED = (_PAGE_DEFAULT | PTE_USER | PTE_RDONLY |
               PTE_NG | PTE_PXN | PTE_UXN | PTE_WRITE)
PAGE_SHARED_EXEC = (_PAGE_DEFAULT | PTE_USER | PTE_RDONLY |
                    PTE_NG | PTE_PXN | PTE_WRITE)
PAGE_READONLY = (_PAGE_DEFAULT | PTE_USER | PTE_RDONLY |
                 PTE_NG | PTE_PXN | PTE_UXN)
PAGE_READONLY_EXEC = (_PAGE_DEFAULT | PTE_USER | PTE_RDONLY | PTE_NG | PTE_PXN)


class PageEntry:
    # 表项内容分成指向物理地址和属性两个部分
    def __init__(self, phys, prot):
        self._phys = phys
        self._prot = prot

    @property
    def phys(self):
        return self._phys

    @property
    def prot(self):
        return self._prot

    def DumpString(self):
        # 通过加法将地址和属性合并在一起
        return "{0:#016x} + {1:#016x}".format(self._phys, self._prot)


class TableEntry:
    # 表项内容分成下级表地址和属性两个部分
    def __init__(self, table, prot):
        self._table = table
        self._prot = prot

    @property
    def prot(self):
        return self._prot

    @property
    def table(self):
        return self._table

    def DumpString(self):
        # 通过加法将地址和属性合并在一起
        return "{0} + {1:#016x}".format(self._table.name, self._prot)

class TableType(Enum):
    PGD = 1
    PUD = 2
    PMD = 3
    PTE = 4

class PageTable:
    def __init__(self, name, tab):
        self._name = name
        self._tab = tab

    @property
    def name(self):
        return self._name

    def Dump(self, f):
        f.write(".align IVY_CFG_PAGE_SHIFT\n")
        f.write("{}:\n".format(self._name))
        for entry in self._tab:
            if entry is None:
                f.write("\t.quad 0\n")
            else:
                f.write("\t.quad {}\n".format(entry.DumpString()))

        # 递归Dump下级表
        for entry in self._tab:
            if entry is not None and isinstance(entry, TableEntry):
                entry.table.Dump(f)


class PageTableAllocator:
    def __init__(self, ptrs_per_pgd, ptrs_per_pud, ptrs_per_pmd, ptrs_per_pte, name_prefix: str = ''):
        self._sn = {}
        self._ptr_num = {}
        self._ptr_num[TableType.PGD] = ptrs_per_pgd
        self._ptr_num[TableType.PUD] = ptrs_per_pud
        self._ptr_num[TableType.PMD] = ptrs_per_pmd
        self._ptr_num[TableType.PTE] = ptrs_per_pte
        self._tables = []
        self.name_prefix = name_prefix

    def Alloc(self, table_type):
        if table_type not in self._sn:
            self._sn[table_type] = 0
        ret = PageTable(
            self.name_prefix + table_type.name+str(self._sn[table_type]), [None]*self._ptr_num[table_type])
        self._sn[table_type] += 1

        # 记录所有分配的页表，可以在这里输出
        self._tables.append(ret)
        return ret

    # def Dump(self):
    #     for pt in self._tables:
    #         pt.Dump(sys.stdout)

# 类似页表内迭代器
class PageTablePointer:
    def __init__(self, pt, idx=0):
        self._pt = pt
        self._idx = idx

    # 不论表项为page还是table，都可以获取prot
    # def GetProt(self):
    #     return self._pt._tab[self._idx].prot

    # 获取当前表项指向的下级表，要求该表项必须为table项，否则会报错
    # def GetNextTable(self):
    #     return self._pt._tab[self._idx]._table

    # 获取当前表项的值，可能为None，PageEntry和TableEntry，只要不是None，即为有效表项
    def Value(self):
        return self._pt._tab[self._idx]

    # 设置当前项为page或是block
    def SetPage(self, phys, prot):
        self._pt._tab[self._idx] = PageEntry(phys, prot)

    # 设置当前表项指向下一级页表
    def Populate(self, tb, prot):
        self._pt._tab[self._idx] = TableEntry(tb, prot)

    # def Write(self, v):
    #     self.Set(v)
    #     if type(v) == int:
    #         GenMemWrite(self._tab.base + self._idx*8, v)
    #     else:
    #         # prot table_addr
    #         GenMemWrite(self._tab.base + self._idx*8, v._tab.base)
    #         # print("write addr {:X} table value {:X}".format(self._tab.base + self._idx*8, v._tab.base))

    def Offset(self, off):
        return PageTablePointer(self._pt, self._idx+off)

    def Next(self):
        return PageTablePointer(self._pt, self._idx+1)
    

class Flag(IntFlag):
    # 禁用巨页
    NO_BLOCK_MAPPINGS = 1
    # 禁用连续页标志
    NO_CONT_MAPPINGS = 2

@dataclass
class Config:
    page_shift: int = 16
    va_bits: int = 48

class PageTableGen:
    def __init__(self, cfg: Config, prefix: str = ''):
        self.name_prefix = prefix
        self._page_shift = cfg.page_shift
        self._va_bits = cfg.va_bits

        avail_page_shifts = [12, 14, 16]
        if self._page_shift not in avail_page_shifts:
            raise Exception(f'the page shift shoule be in {avail_page_shifts}')
        
        if self._va_bits != 48:
            raise Exception(f'only 48-bit addressing is supported now')

        self._arm64_64k_pages = False
        if self._page_shift == 16:
            self._arm64_64k_pages = True

        self._arm64_16k_pages = False
        if self._page_shift == 14:
            self._arm64_16k_pages = True

        self._page_size = 1<< self._page_shift
        self._page_mask = (~(self._page_size-1) & PHY_ADDR_MASK)
        self._page_mask = (~(self._page_size-1) & PHY_ADDR_MASK)
        self._page_off_mask = (self._page_size-1)

        self._page_levels = ARM64_HW_PGTABLE_LEVELS(self._va_bits, self._page_shift)
        self._ptrs_per_pte = (1 << (self._page_shift - 3))

        if self._page_levels > 2:
            self._pmd_shift = ARM64_HW_PGTABLE_LEVEL_SHIFT(2, self._page_shift)
            self._pmd_size = (1 << self._pmd_shift)
            self._pmd_mask = (~(self._pmd_size-1)) & PHY_ADDR_MASK
            self._ptrs_per_pmd = self._ptrs_per_pte

        if self._page_levels > 3:
            self._pud_shift = ARM64_HW_PGTABLE_LEVEL_SHIFT(1, self._page_shift)
            self._pud_size = (1 << self._pud_shift)
            self._pud_mask = (~(self._pud_size-1)) & PHY_ADDR_MASK
            self._ptrs_per_pud = self._ptrs_per_pte

        self._pgdir_shift = ARM64_HW_PGTABLE_LEVEL_SHIFT(4 - self._page_levels, self._page_shift)
        self._pgdir_size = (1 << self._pgdir_shift)
        self._pgdir_mask = (~(self._pgdir_size-1) & PHY_ADDR_MASK)
        self._ptrs_per_pgd = (1 << (self._va_bits - self._pgdir_shift))

        self._section_shift = self._pmd_shift
        self._section_size = (1 << self._section_shift)
        self._section_mask = (~(self._section_size - 1)) & PHY_ADDR_MASK

        if self._page_shift == 16:
            self._cont_pte_shift = 5
            self._cont_pmd_shift = 5
        elif self._page_shift == 14:
            self._cont_pte_shift = 7
            self._cont_pmd_shift = 5
        else:
            self._cont_pte_shift = 4
            self._cont_pmd_shift = 4
        
        self._cont_ptes = (1 << self._cont_pte_shift)
        self._cont_pte_size = (self._cont_ptes * self._page_size)
        self._cont_pte_mask = ((~(self._cont_pte_size-1)) & PHY_ADDR_MASK)
        self._cont_pmds = (1 << self._cont_pmd_shift)
        self._cont_pmd_size = (self._cont_pmds * self._pmd_size)
        self._cont_pmd_mask = ((~(self._cont_pmd_size - 1)) & PHY_ADDR_MASK)

        self._pte_addr_low = ((1 << (48 - self._page_shift) - 1) << self._page_shift)
        self._pte_addr_mask = self._pte_addr_low

        if not self._page_levels > 3:
            self._pud_offset = self._pud_offset_folded

        if not (self._arm64_64k_pages or self._page_levels < 3):
            self._pud_sect = self._pud_sect_enable
            self._pud_table = self._pud_table_enable

        if self._page_levels <= 3:
            self._pud_shift = self._pgdir_shift
            self._pud_size = (1 << self._pud_shift)
            self._pud_mask = (~(self._pud_size-1)) & PHY_ADDR_MASK
            self._ptrs_per_pud = 1

        if self._page_levels <= 2:
            self._pmd_shift = self._pud_shift
            self._ptrs_per_pmd = 1
            self._pmd_size = (1 << self._pmd_shift)
            self._pmd_mask = (~(self._pmd_size - 1)) & PHY_ADDR_MASK

        if self._page_levels > 3:
            self._pud_addr_end = self._pud_addr_end_gt3
        else:
            self._pud_addr_end = self._pud_addr_end_le3

        if self._page_levels > 2:
            self._pmd_addr_end = self._pmd_addr_end_gt2
        else:
            self._pmd_addr_end = self._pmd_addr_end_le2

        if self._page_levels > 3:
            self._pgd_none = self._pgd_none_gt3
        else:
            self._pgd_none = self._pgd_none_le3

        if self._page_levels > 2:
            self._pud_none = self._pud_none_gt2
        else:
            self._pud_none = self._pud_none_le2
            self._pud_offset = self._pud_offset_folded

        self.mair_el1_val = MAIR(0x00, MT_DEVICE_nGnRnE) | MAIR(0x04, MT_DEVICE_nGnRE) | MAIR(
            0x0c, MT_DEVICE_GRE) | MAIR(0x44, MT_NORMAL_NC) | MAIR(0xff, MT_NORMAL) | MAIR(0xbb, MT_NORMAL_WT)
        
        # PTWs cacheable, inner/outer WBWA
        self._tcr_cache_flags = TCR_IRGN_WBWA | TCR_ORGN_WBWA
        self._tcr_smp_flags = TCR_SHARED

        if self._arm64_64k_pages:
            self._tcr_tg_flags = TCR_TG0_64K | TCR_TG1_64K
        elif self._arm64_16k_pages:
            self._tcr_tg_flags = TCR_TG0_16K | TCR_TG1_16K
        else:
            self._tcr_tg_flags = TCR_TG0_4K | TCR_TG1_4K

        self._tcr_kaslr_flags = 0
        self._tcr_ips = (2 << 32)
        self.tcr_el1_val = TCR_TxSZ(self._va_bits) | self._tcr_cache_flags | self._tcr_smp_flags | \
            self._tcr_tg_flags | self._tcr_kaslr_flags | TCR_ASID16 | \
            TCR_TBI0 | TCR_A1 | self._tcr_ips
        
        self.sctlr_el1_val = (SCTLR_ELx_M | SCTLR_ELx_C | SCTLR_ELx_SA |
                SCTLR_EL1_SA0 | SCTLR_EL1_SED | SCTLR_ELx_I |
                SCTLR_EL1_DZE | SCTLR_EL1_UCT | SCTLR_EL1_NTWI |
                SCTLR_EL1_NTWE | SCTLR_ELx_IESB | SCTLR_EL1_SPAN |
                ENDIAN_SET_EL1 | SCTLR_EL1_UCI | SCTLR_EL1_RES1)
        
        self._pt_allocator = PageTableAllocator(self._ptrs_per_pgd, self._ptrs_per_pud, self._ptrs_per_pmd, self._ptrs_per_pte, self.name_prefix)
        self._pgd = self._pt_allocator.Alloc(TableType.PGD)
        self._pgdp = PageTablePointer(self._pgd)

    #  the the numerical offset of the PTE within a range of CONT_PTES
    def _cont_range_offset(self, addr):
        return (addr >> self._page_shift) & (self._cont_ptes - 1)
    
    # ref arch/asm-generic/pgtable.h
    # addr在一个pgd项的结尾地址，如果end更大，则到达pgd项边界
    def _pgd_addr_end(self, addr, end):
        boundary = (addr + self._pgdir_size) & self._pgdir_mask
        return boundary if (boundary - 1 < end - 1) else end

    # if PGTABLE_LEVELS > 3:
    def _pud_addr_end_gt3(self, addr, end):
        boundary = (addr + self._pud_size) & self._pud_mask
        return boundary if (boundary - 1 < end - 1) else end

    # if PGTABLE_LEVELS > 2:
    def _pmd_addr_end_gt2(self, addr, end):
        boundary = (addr + self._pmd_size) & self._pmd_mask
        return boundary if (boundary - 1 < end - 1) else end
    
    # ref arch/arm64/include/asm/pgtable.h
    def _pgd_index(self, addr):
        return (((addr) >> self._pgdir_shift) & (self._ptrs_per_pgd - 1))

    def _pte_cont_addr_end(self, addr, end):
        boundary = (addr + self._cont_pte_size) & self._cont_pte_mask
        return boundary if (boundary - 1 < end - 1) else end

    def _pmd_cont_addr_end(self, addr, end):
        boundary = (addr + self._cont_pmd_size) & self._cont_pmd_mask
        return boundary if (boundary - 1 < end - 1) else end

    # if PGTABLE_LEVELS > 3:
    def _pgd_none_gt3(self, pgd):
        return not pgd

    def _pud_index(self, addr):
        return (addr >> self._pud_shift) & (self._ptrs_per_pud - 1)

    # 从pgdp获取对应pud表，并返回指向addr地址的首个pud表项指针
    def _pud_offset(self, pgdp, addr):
        # 需要根据pgdp指向的pud表值读取到pud表格对应项的指针
        pgd_val = pgdp.Value()
        return PageTablePointer(pgd_val.table, self._pud_index(addr))
    # else:
    # 折叠
    def _pud_offset_folded(self, pgdp, addr):
        return pgdp
    
    # if PGTABLE_LEVELS > 2:
    def _pud_none_gt2(self, pud):
        return not pud

    # def pud_present(pud):
    #     return pte_present(pud_pte(pud))

    def _set_pud(self, pudp, pud):
        pudp.Write(pud)
        # dsb(ishst);
        # isb();

    def _pud_clear(self, pudp):
        self._set_pud(pudp, 0)

    def _pmd_index(self, addr):
        return (addr >> self._pmd_shift) & (self._ptrs_per_pmd - 1)

    def _pmd_offset(self, pudp, addr):
        pud_val = pudp.Value()
        return PageTablePointer(pud_val.table, self._pmd_index(addr))
    # else:
    def _pmd_offset_folded(self, pudp, addr):
        return pudp


    # if ARM64_64K_PAGES or PGTABLE_LEVELS < 3:
    def _pud_sect(self, pud):
        return False

    def _pud_table(self, pud):
        return True
    # else:
    def _pud_sect_enable(self, pud):
        return (pud & PUD_TYPE_MASK) == PUD_TYPE_SECT

    def _pud_table_enable(self, pud):
        return (pud & PUD_TYPE_MASK) == PUD_TYPE_TABLE

    def _pmd_none(self, pmd):
        return not pmd

    def _pmd_table(self, pmd):
        return (pmd & PMD_TYPE_MASK) == PMD_TYPE_TABLE

    def _pmd_sect(self, pmd):
        return (pmd & PMD_TYPE_MASK) == PMD_TYPE_SECT

    def _set_pmd(self, pmdp, pmd):
        pmdp.Write(pmd)
        # dsb(ishst)
        # isb()

    def _pmd_clear(self, pmdp):
        self._set_pmd(pmdp, 0)

    def _pte_index(self, addr):
        return (addr >> self._page_shift) & (self._ptrs_per_pte - 1)

    def _pte_set_fixmap_offset(self, pmdp, addr):
        pmd_val = pmdp.Value()
        return PageTablePointer(pmd_val.table, self._pte_index(addr))
        # return pmdp.Get().Offset(pte_index(addr))

    def _mk_sect_prot(self, prot):
        return prot & (~PTE_TABLE_BIT)

    def _pmd_pfn(self, pmd):
        return (pmd & self._pmd_mask) >> self._page_shift

    def _pfn_pmd(self, pfn, prot):
        return (pfn << self._page_shift) | prot

    def _pud_pfn(self, pud):
        return (pud & self._pud_mask) >> self._page_shift

    def _pfn_pud(self, pfn, prot):
        return (pfn << self._page_shift) | prot
    
    # ref include/asm-generic/pgtable-nopud.h
    # # no pud
    # if PGTABLE_LEVELS <= 3:
    def _pud_addr_end_le3(self, addr, end):
        return end

    def _pgd_none_le3(self, pgd):
        return False

    # ref include/asm-generic/pgtable-nopmd.h
    # if PGTABLE_LEVELS <= 2:
    def _pmd_addr_end_le2(self, addr, end):
        return end

    def _pud_none_le2(self, pud):
        return False
    
    def _pfn_align(self, x):
        return (x + (self._page_size-1)) & self._page_mask

    def _pfn_up(self, x):
        return (x + self._page_size - 1) >> self._page_shift
        
    def _pfn_down(self, x):
        return x >> self._page_shift

    def _pfn_phys(self, x):
        return x << self._page_shift
        
    def _phys_pfn(self, x):
        return x >> self._page_shift
        
    # ref other.h
    # to align the pointer to the (next) page boundary
    def _page_align(self, addr):
        return (addr + self._page_size - 1) & self._page_mask

    # ref arch/arm64/mm/mmu.c
    # 内核初始页表建立，包括所有存储的线性映射，内核代码和数据区
    # 支持对地址范围的映射，支持巨页和连续页
    def _pud_set_huge(self, pudp, phys, prot):
        sect_prot = PUD_TYPE_SECT | self._mk_sect_prot(prot)
        pudp.SetPage(phys, sect_prot)
        # new_pud = pfn_pud(PHYS_PFN(phys), sect_prot)
        # set_pud(pudp, new_pud)

    def _pmd_set_huge(self, pmdp, phys, prot):
        sect_prot = PMD_TYPE_SECT | self._mk_sect_prot(prot)
        pmdp.SetPage(phys, sect_prot)
        # new_pmd = pfn_pmd(PHYS_PFN(phys), sect_prot)
        # set_pmd(pmdp, new_pmd)

    def _init_pte(self, pmdp, addr, end, phys, prot):
        ptep = self._pte_set_fixmap_offset(pmdp, addr)
        while True:
            old_pte = ptep.Value()
            ptep.SetPage(phys, prot)
            phys += self._page_size
            ptep = ptep.Next()
            addr += self._page_size
            if addr == end:
                break

    def _alloc_init_cont_pte(self, pmdp, addr, end, phys, prot, pgtable_alloc, flags):
        pmd_val = pmdp.Value()

        if self._pmd_none(pmd_val):
            pte = pgtable_alloc(TableType.PTE)
            pmdp.Populate(pte, prot | PMD_TYPE_TABLE)

        while True:
            _prot = prot
            next = self._pte_cont_addr_end(addr, end)

            # 支持页连续标志
            if (addr | next | phys) & (~self._cont_pte_mask & PHY_ADDR_MASK) == 0 and not (flags & Flag.NO_CONT_MAPPINGS):
                _prot = prot | PTE_CONT

            self._init_pte(pmdp, addr, next, phys, _prot)

            phys += next - addr
            addr = next
            if addr == end:
                break

    def _init_pmd(self, pudp, addr, end, phys, prot, pgtable_alloc, flags):
        pmdp = self._pmd_offset(pudp, addr)

        while True:
            # old_pmd = pmdp.Get()
            next = self._pmd_addr_end(addr, end)

            if (addr | next | phys) & (~self._section_mask & PHY_ADDR_MASK) == 0 and not (flags & Flag.NO_BLOCK_MAPPINGS):
                self._pmd_set_huge(pmdp, phys, prot)
            else:
                self._alloc_init_cont_pte(pmdp, addr, next, phys, prot, pgtable_alloc, flags)

            phys += next - addr
            pmdp = pmdp.Next()
            addr = next
            if addr == end:
                break

    # 带连续页标志能力
    def _alloc_init_cont_pmd(self, pudp, addr, end, phys, prot, pgtable_alloc, flags):
        pud_val = pudp.Value()
        if self._pud_none(pud_val):
            pmd = pgtable_alloc(TableType.PMD)
            pudp.Populate(pmd, prot | PUD_TYPE_TABLE)
            # pud = pudp.Get()

        while True:
            _prot = prot
            next = self._pmd_cont_addr_end(addr, end)
            if (addr | next | phys) & (~self._cont_pmd_mask) == 0:
                _prot |= PTE_CONT

            # pmd表通过pudp获取，支持折叠
            self._init_pmd(pudp, addr, next, phys, _prot, pgtable_alloc, flags)

            phys += next - addr
            addr = next
            if addr == end:
                break

    def _use_1G_block(self, addr, next, phys):
        if self._page_shift != 12:
            return False
        if (addr | next | phys) & (~self._pud_mask & PHY_ADDR_MASK) != 0:
            return False
        return True

    def _alloc_init_pud(self, pgdp, addr, end, phys, prot, pgtable_alloc, flags):
        pgd_val = pgdp.Value()
        # 如果当前pgd表项为空，则需要分配新的pud表
        if self._pgd_none(pgd_val):
            pud = pgtable_alloc(TableType.PUD)
            # 设置pgd当前表项指向下一级pud表
            pgdp.Populate(pud, prot | PUD_TYPE_TABLE)
            # 建立指向pud表的迭代器
            # pudp = PageTablePointer(pud)
            # GenComment("populate new pudp")
            # pgdp.Write(pudp)
            # populate

        # 根据地址在pgd表中找对应的pud表项
        # 支持pgd pud折叠
        pudp = self._pud_offset(pgdp, addr)

        while True:
            # old_pud = pudp.Get()
            next = self._pud_addr_end(addr, end)

            if self._use_1G_block(addr, next, phys) and not (flags & Flag.NO_BLOCK_MAPPINGS):
                self._pud_set_huge(pudp, phys, prot)
            else:
                self._alloc_init_cont_pmd(pudp, addr, next, phys,
                                    prot, pgtable_alloc, flags)

            phys += next - addr
            pudp = pudp.Next()
            addr = next
            if addr == end:
                break

    # 仅用于创建建立以后不再修改的虚地址区域，页表数据会通过后门初始化，支持连续页标志，所以其中的虚地址空间不能
        
    # ref mm/vmalloc.c
    # vmap支持将一组物理页映射到从内核地址空间分配的一个连续虚地址内，由于物理页不一定连续，不支持巨页和连续页
    # vunmap支持将一段内核虚地址从内核页表卸载，实际上即使不是通过vmap映射的也可以通过该函数卸载
        
    # ref arch/arm64/mm/ioremap.c lib/ioremap.c
    # 前者提供体系结构特定的ioremap和iounmap，在arm64中ioremap的实现通过get_vm_area_caller函数从内核首先分配虚地址空间，然后通过lib/ioremap.c内的
    # ioremap函数将所需要物理地址映射到该虚地址空间，iounmap则直接使用vunmap
    # vunmap只有一个地址参数，因为每段虚地址都是get_vm_area_caller函数所分配，map和unmap的单位必须是分配的一个完整虚地址空间，不允许部分map或是部分unmap
    # lib/ioremap.c中的ioremap函数实现支持巨页，不支持连续地址空间
    # 实际上三处map函数实现类似
    # 需要注意的是，在map时，需要保证map指定的地址空间当前是没有任何占用的，所以只要空间合适支持巨页时，就会设置巨页
    # 同样的虚地址空间如果要重复使用，必须原先map的空间unmap，然后再map新的虚地址空间，这在vmap和vunmap函数中通过以单个vm_area为单位
    # 进行map和unmap来解决

    # 实现两个函数，对范围进行映射，map函数支持巨页，存储分配静态完成，数据修改运行时完成
    # 为了避免对新分配存储的清0操作
    def _map_range(self, pgdp, phys, virt, size, prot, pgtable_alloc, flags):
        # 从头部偏移到对应虚地址范围的第一个pgd项
        pgdp = pgdp.Offset(self._pgd_index(virt))
        # 起始物理地址和虚拟地址向下对其到页边界
        phys &= self._page_mask
        addr = virt & self._page_mask
        # 长度向上对齐到下一个页边界
        length = self._page_align(size + (virt & self._page_off_mask))

        end = addr + length
        while True:
            next = self._pgd_addr_end(addr, end)

            self._alloc_init_pud(pgdp, addr, next, phys, prot, pgtable_alloc, flags)

            phys += next - addr
            pgdp = pgdp.Next()
            addr = next
            if addr == end:
                break


    # 暂时在静态条件没有unmap的需求
    # def unmap_pte_range(pmdp, addr, end):
    #     ptep = pte_set_fixmap_offset(pmdp, addr)
    #     while True:
    #         # clear
    #         ptep.Write(0)
    #         ptep = ptep.Next()
    #         addr = addr + PAGE_SIZE
    #         if addr == end:
    #             break


    # def unmap_pmd_range(pudp, addr, end):
    #     pmdp = pmd_offset(pudp, addr)

    #     while True:
    #         next = pmd_addr_end(addr, end)
    #         if pmd_clear_huge(pmdp) or pmd_none(pmdp.Get()):
    #             pass
    #         else:
    #             unmap_pte_range(pmdp, addr, next)

    #         pmdp = pmdp.Next()
    #         addr = next
    #         if addr == end:
    #             break


    # def unmap_pud_range(pgdp, addr, end):
    #     pudp = pud_offset(pgdp, addr)

    #     while True:
    #         next = pud_addr_end(addr, end)
    #         if pud_clear_huge(pudp) or pud_none(pudp.Get()):
    #             pass
    #         else:
    #             unmap_pmd_range(pudp, addr, next)

    #         pudp = pudp.Next()
    #         addr = next
    #         if addr == end:
    #             break

    # unmap


    # def unmap_range(pgdp, addr, size):
    #     pgdp = pgdp.Offset(pgd_index(addr))
    #     end = addr + size
    #     while True:
    #         next = pgd_addr_end(addr, end)
    #         if pgd_none(pgdp.Get()):
    #             pass
    #         else:
    #             unmap_pud_range(pgdp, addr, next)

    #         pgdp = pgdp.Next()
    #         addr = next
    #         if addr == end:
    #             break

    # def pud_clear_huge(pudp):
    #     if not pud_sect(pudp.Get()):
    #         return False
    #     pud_clear(pudp)
    #     return True


    # def pmd_clear_huge(pmdp):
    #     if not pmd_sect(pmdp.Get()):
    #         return False
    #     pmd_clear(pmdp)
    #     return True

    # map unmap

    def MapRange(self, phys, virt, size, prot, flags=0):
        self._map_range(self._pgdp, phys, virt, size, prot,
                        self._pt_allocator.Alloc, flags)

    def DumpToFile(self, filename):
        with open(filename, "w") as f:
            f.write("#include \"ivy_cfg.h\"\n")
            f.write(".section \".pt_data\", \"ad\"\n")
            f.write(f".global {self.name_prefix}PGD0\n")
            self._pgd.Dump(f)

UVA_START = 0xFFFF000000000000
class UserPageTable:
    def __init__(self, page_size: int) -> None:
        ptg_cfg = Config()
        if page_size == 64*1024*1024:
            ptg_cfg.page_shift = 16
        elif page_size == 16*1024*1024:
            ptg_cfg.page_shift = 14
        else:
            ptg_cfg.page_shift = 12
        self.ptg = PageTableGen(ptg_cfg, 'USER_')
    
    def map_range(self, pa, va, size, prot, flags=0):
        va = va & 0xFFFFFFFFFFFFFFFF
        if va < UVA_START:
            logger.critical(f'user va must be larger than {UVA_START:#x}')
            sys.exit(1)
        self.ptg.MapRange(pa, va, size, prot, flags)

    def dumpf(self, filename:str):
        self.ptg.DumpToFile(filename)
