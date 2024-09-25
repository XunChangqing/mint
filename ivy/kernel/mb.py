# author: zuoqian
# Copyright 2023. All rights reserved.

import math
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ref include/linux/memblock.h, mm/memblock.c, drivers/of/fdt.c
PHYS_ADDR_MAX = 0xFFFFFFFFFFFFFFFF

def _clamp(n, smallest, largest):
    return max(smallest, min(n, largest))

#
#  round_up - round up to next specified power of 2
#  @x: the value to round
#  @y: multiple to round up to (must be a power of 2)
#
#  Rounds @x up to next multiple of @y (which must be a power of 2).
#  To perform arbitrary rounding up, use roundup() below.
#
def _round_up(n, align):
    return align * math.ceil(n / align)

def _MemBlockCapSize(base, size):
    return min(size, PHYS_ADDR_MAX-base)

def _MemBlockAddrsOverlap(base1, size1, base2, size2) -> bool:
    return (base1 < (base2 + size2)) and (base2 < (base1 + size1))

# 存储区间，寄地址，尺寸，所属numa节点
@dataclass
class MemBlockRegion:
    base:int
    size:int
    nid:int = None

# 一种memblock类型，在linux中highmem、dma32等不同
class MemBlockType:
    def __init__(self):
        self.regions = []

    def MergeRegions(self):
        ridx = 0
        while ridx < len(self.regions)-1:
            rthis = self.regions[ridx]
            rnext = self.regions[ridx+1]
            if rthis.base + rthis.size != rnext.base or rthis.nid != rnext.nid:
                ridx += 1
                continue
            self.regions.pop(ridx)
            self.regions.pop(ridx)
            self.regions.insert(ridx, MemBlockRegion(
                rthis.base, rthis.size+rnext.size, rthis.nid))
            #    assert(rthis.base + rthis.size <= rnext.base)

    def RemoveRegion(self, r):
        self.regions.pop(r)

    def InsertRegion(self, idx, base, size, node):
        self.regions.insert(idx, MemBlockRegion(base, size, node))

    def OverlapsRegion(self, base, size) -> bool:
        for r in self.regions:
            if _MemBlockAddrsOverlap(base, size, r.base, r.size):
                return True
        return False

    # Add new memblock region [@base, @base + @size) into @type.  The new region
    # is allowed to overlap with existing ones - overlaps don't affect already
    # existing regions.  @type is guaranteed to be minimal (all neighbouring
    # compatible regions are merged) after the addition.
    def AddRange(self, base, size, node):
        size = _MemBlockCapSize(base, size)
        end = base + size

        if not size:
            return

        if not self.regions:
            self.regions.append(MemBlockRegion(base, size, node))
            return

        ridx = 0
        while ridx < len(self.regions):
            rbase = self.regions[ridx].base
            rend = self.regions[ridx].base + self.regions[ridx].size
            if rbase >= end:
                break
            if rend <= base:
                ridx += 1
                continue

            if (rbase > base):
                self.regions.insert(
                    ridx, MemBlockRegion(base, rbase-base, node))
                # skip the current region
                ridx += 1

            base = min(rend, end)
            ridx += 1

        # insert the remaining portion
        if base < end:
            self.regions.insert(ridx, MemBlockRegion(base, end-base, node))

        self.MergeRegions()

    # memblock_isolate_range - isolate given range into disjoint memblocks
    def __IsolateRange(self, base, size):
        size = _MemBlockCapSize(base, size)
        end = base + size
        start_rgn = None
        end_rgn = None

        if not size:
            raise 'size is zero'

        ridx = 0
        while ridx < len(self.regions):
            rbase = self.regions[ridx].base
            rend = rbase + self.regions[ridx].size
            rnode = self.regions[ridx].nid

            if rbase >= end:
                break
            if rend <= base:
                ridx += 1
                continue

            if rbase < base:
                # @rgn intersects from below.  Split and continue
                # to process the next region - the new top half.
                #   |------|-----------------|
                # rbase   base              rend
                self.regions.pop(ridx)
                self.regions.insert(
                    ridx, MemBlockRegion(rbase, base-rbase, rnode))
                self.regions.insert(
                    ridx+1, MemBlockRegion(base, rend-base, rnode))
            elif rend > end:
                # @rgn intersects from above.  Split and redo the
                # current region - the new bottom half.
                #  |-------|--------------|
                # rbase   end            rend
                self.regions.pop(ridx)
                self.regions.insert(ridx, MemBlockRegion(end, rend-end, rnode))
                self.regions.insert(
                    ridx, MemBlockRegion(rbase, end-rbase, rnode))
                # redo the current region
                ridx -= 1
            else:
                # @rgn is fully contained, record it
                if not end_rgn:
                    start_rgn = ridx
                end_rgn = ridx+1
            ridx += 1

        if start_rgn is None or end_rgn is None:
            raise 'failed'

        return start_rgn, end_rgn

    def RemoveRange(self, base, size):
        start_rgn, end_rgn = self.__IsolateRange(base, size)
        self.regions = self.regions[:start_rgn] + self.regions[end_rgn:]

#  Find the first area from *@idx which matches @nid, fill the out
#  parameters, and update *@idx for the next iteration.  The lower 32bit of
#  *@idx contains index into type_a and the upper 32bit indexes the
#  areas before each region in type_b.	For example, if type_b regions
#  look like the following,
#
        # 0:[0-16), 1:[32-48), 2:[128-130)
#
#  The upper 32bit indexes the following regions.
#
        # 0:[0-0), 1:[16-32), 2:[48-128), 3:[130-MAX)
#
#  As both region arrays are sorted, the function advances the two indices
#  in lockstep and returns each intersection.
def _MemRanges(typea, typeb):
    rbidx = 0
    for ra in typea:
        m_start = ra.base
        m_end = ra.base + ra.size

        if not typeb or not typeb.regions:
            yield m_start, m_end

        for rbidx in range(rbidx, len(typeb)+1):
            r_start = typeb[rbidx-1].base + \
                typeb[rbidx-1].size if rbidx > 0 else 0
            r_end = typeb[rbidx].base if rbidx < len(typeb) else PHYS_ADDR_MAX

            if r_start >= m_end:
                break

            # if the two regions intersect, we're done
            if m_start < r_end:
                out_start = max(m_start, r_start)
                out_end = min(m_end, r_end)

                yield out_start, out_end

                if m_end <= r_end:
                    break

def _MemRangesRev(typea, typeb):
    rbidx = len(typeb)
    for ra in reversed(typea):
        m_start = ra.base
        m_end = ra.base + ra.size

        if not typeb or not typeb.regions:
            yield m_start, m_end

        for rbidx in range(rbidx, -1, -1):
            r_start = typeb[rbidx-1].base + \
                typeb[rbidx-1].size if rbidx > 0 else 0
            r_end = typeb[rbidx].base if rbidx < len(typeb) else PHYS_ADDR_MAX

            if r_start >= m_end:
                break

            # if the two regions intersect, we're done
            if m_start < r_end:
                out_start = max(m_start, r_start)
                out_end = min(m_end, r_end)

                yield out_start, out_end

                if m_end <= r_end:
                    break

# TODO
# 支持随机分配
class MemBlock:
    def __init__(self):
        # 采用类似linux内核实现方法，可用内存和保留内存分开维护
        # TOFIX
        # 为什么不只维护一个可用内存，分配以后删除？
        # 貌似，如果删除，那么原始可用内存的属性，例如节点id，必须要保存，不能简单删除某个region
        # 否则释放时难以恢复该信息
        # 可用存储
        self.memory = MemBlockType()
        # 保留存储
        self.reserved = MemBlockType()

    # 新增保留的存储段，可能一开始就保留，也可能是分配以后保留
    def Reserve(self, base, size):
        self.reserved.AddRange(base, size, None)

    def AddNode(self, base, size, nid):
        self.memory.AddRange(base, size, nid)

    # 新增可用内存，用于一开始初始化
    def Add(self, base, size):
        self.memory.AddRange(base, size, 0)

    # 在start和end范围内从低向上查找size(对齐到align)的区间,返回起始位置
    def FreeRanges(self, nid = None):
        mregions = self.memory.regions
        rregions = self.reserved.regions
        midx = 0
        ridx = 0
        while midx < len(mregions) and ridx <= len(rregions):
            if nid is not None and mregions[midx].nid != nid:
                midx += 1
                continue

            m_start = mregions[midx].base
            m_end = mregions[midx].base + mregions[midx].size
            m_nid = mregions[midx].nid

            # 对reserved region取反
            if ridx <= 0:
                r_start = 0
            else:
                r_start = rregions[ridx-1].base + rregions[ridx-1].size

            if ridx >= len(rregions):
                r_end = PHYS_ADDR_MAX
            else:
                r_end = rregions[ridx].base

            # 交集
            o_start = max(m_start, r_start)
            o_end = min(m_end, r_end)

            if o_end > o_start:
                yield o_start, o_end, m_nid

            # 先结束的索引先增加
            if m_end <= r_end:
                midx += 1
            else:
                ridx += 1

    # 获取可用空间的最低地址
    def FreeLowAddr(self):
        for this_start, this_end, _ in self.FreeRanges():
            return this_start

    def FindRangeBottomUp(self, size, align, start, end, nid):
        for this_start, this_end, _ in self.FreeRanges(nid):
            # logger.debug("{:x} {:x}".format(this_start, this_end))
            this_start = _clamp(this_start, start, end)
            this_end = _clamp(this_end, start, end)
            cand = _round_up(this_start, align)
            if cand < this_end and this_end - cand >= size:
                return cand

    # def FindRangeTopDown(start, end, size, align):
    #     pass

    # 在指定start和end之间，为nid分配尺寸为size（对齐到align）存储
    # nid为None表示任意节点
    def AllocRangeNid(self, size, align, start, end, nid):
        if end is None:
            end = PHYS_ADDR_MAX
            
        found = self.FindRangeBottomUp(size, align, start, end, nid)
        if found is None:
            raise Exception("alloc failed")

        size_aligned = size
        self.Reserve(found, size_aligned)
        return found

    # 在指定start和end之间，分配存储，尺寸为size，分配初始地址对齐到align
    def AllocRange(self, size, align, start, end):
        return self.AllocRangeNid(size, align, start, end, None)

    def Alloc(self, size, align):
        return self.AllocRange(size, align, 0, PHYS_ADDR_MAX)

    def AllocNid(self, size, align, nid):
        return self.AllocRangeNid(size, align, 0, PHYS_ADDR_MAX, nid)

    def Free(self, base, size):
        self.reserved.RemoveRange(base, size)
