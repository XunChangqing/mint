# head.S
建立id map和swap map
前者一一映射，写入ttbr0，后者将内核代码映射到指定虚地址，两者页表空间都是静态分配，在lds中指定尺寸
内核所处物理地址直接通过adr即可获得，虚地址宏定义确定。
Id映射保证内核在虚实地址转换时保证正确，首先转到同地址虚地址执行，然后转到swap map的虚地址执行
最后设置一下sp，就进入start_kernel@main.c
```
	. = ALIGN(PAGE_SIZE);
	idmap_pg_dir = .;
	. += IDMAP_DIR_SIZE;

	swapper_pg_dir = .;
	. += SWAPPER_DIR_SIZE;
	swapper_pg_end = .;
    
    _end = .;
```

*** 疑惑 ***
swap页表所需要的尺寸与内核实际尺寸有关，因为该页表必须完全覆盖内核尺寸，这里有些疑惑和矛盾，因为swap页表尺寸依赖于_end的位置，但是_end的位置又会依赖与swap页表具体的尺寸，不知道这里为什么是正确的???
```c
#define SWAPPER_DIR_SIZE (PAGE_SIZE * EARLY_PAGES(KIMAGE_VADDR + TEXT_OFFSET, _end))
```

# setup_arch
start_kernel中存储相关的调用首先是setup_arch，这是体系结构特定的建立函数
arch/arm64/setup.c

## early_fixmap_init()
fixmap初始化，此时除了内核代码所处区域其他存储区域无法访问，该fixmap用于建立其他页面过程中，访问新分配的物理地址时使用，只需要映射一个pud,pmd,pte既可以，fixmap的虚地址在内核地址空间是确定的，页表空间通过全局数据静态分配
```c
static pte_t bm_pte[PTRS_PER_PTE] __page_aligned_bss;
static pmd_t bm_pmd[PTRS_PER_PMD] __page_aligned_bss __maybe_unused;
static pud_t bm_pud[PTRS_PER_PUD] __page_aligned_bss __maybe_unused;
```
bm指boot_memory
注意这里没有pgd，因为直接使用swap dir pgd，在内核地址空间映射物理地址

## arm64_memblock_init()
通过分析fdt，将所有可用物理存储建立到boot阶段物理存储管理器memblock中，后续boot过程即可通过memblock分配物理页

## pagint_init()
这个函数非常重要，通过memblock分配物理页，通过fixmap映射分配到的物理页进行访问，将kernel重新细粒度映射到内核空间，将所有物理内存映射到线性地址空间。
该函数完成以后，所有物理内存就可以通过线性地址空间访问，不再需要fixmap
Bootmem_init
该函数通过调用zone_sizes_init为所有物理内存分配page数据结果空间，存储模型有flat、discontiguous、sparse三种，第二种一般不在使用，关于三种的不同可以参考相关文献。
Zone_sizes_init调用的核心函数为free_area_init_nodes，为numa的每个node建立free area，即所有可用物理空间的page结构数组，起始状态下这个page都是不可用的。

# mm_init() @ main.c
## mem_init()
通过free_all_bootmem将所有boot阶段存储管理中未使用的物理存储，通过__free_pages_bootmem释放到基于buddy分配算法的最终运行时物理页分配器中。
完成以后alloc_pages，get_free_pages等函数可以使用。

## kmem_cache_init
初始化基于slab的内核存储分配器，完成以后kmalloc、kfree函数可以使用。

## vmalloc_init
初始化内核vmalloc相关依赖，完成以后vmalloc可以使用，通过ioremap应该也可以使用。

# 内核地址计算
## 内核符号虚地址与物理地址
Head.S中会记录内核起始物理地址与内核起始虚地址的kimage_offset，之后根据这个offset即可以进行转换

## 线性映射虚地址与物理地址
根据线性虚地址映射的起始物理地址可以简单计算

## 内核符号的线性虚地址别名
先转换为物理地址，然后再转换为线性映射虚地址
lm_alias
