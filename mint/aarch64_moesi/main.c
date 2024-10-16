#include <stdint.h>

#include <ivy/xrt.h>
#include <ivy/print.h>

void mango_core_main_func(uint64_t core_id);

// asm volatile("swp{suffix} %{r}1, %{r}0, [%2]" : "=&r"(ov) : "r"
// ({new_int_val:#x}), "r" ({self.addr:#x}));

// #define ID_MMFR2_CCIDX_SHIFT (20)
// #define ID_MMFR2_CCIDX_MASK (0xF)

// uint64_t associativity;
// uint64_t num_sets;
// uint64_t assoc_shift;
// uint64_t index_mask;

// static void dc_init() {
//   uint64_t id_mmfr2;
//   asm volatile("mrs %x0, id_aa64mmfr2_el1" : "=&r"(id_mmfr2) :);
//   uint64_t id_mmfr2_ccidx =
//       ((id_mmfr2 >> ID_MMFR2_CCIDX_SHIFT) & ID_MMFR2_CCIDX_MASK);

//   uint64_t ccsidr_assoc_shift;
//   uint64_t ccsidr_assoc_mask;
//   uint64_t ccsidr_nsets_shift;
//   uint64_t ccsidr_nests_mask;

//   if (id_mmfr2_ccidx == 0) {
//     // 3,10
//     ccsidr_assoc_shift = 3;
//     ccsidr_assoc_mask = 0x3FF;
//     // 13,15
//     ccsidr_nsets_shift = 13;
//     ccsidr_nests_mask = 0x7FFF;
//   } else {
//     // 3,21
//     ccsidr_assoc_shift = 3;
//     ccsidr_assoc_mask = 0x1FFFFF;
//     // 32,24
//     ccsidr_nsets_shift = 32;
//     ccsidr_nests_mask = 0xFFFFFF;
//   }

//   asm volatile("msr csselr_el1, %x0" ::"r"(0));
//   uint64_t ccsidr;
//   asm volatile("mrs %x0, ccsidr_el1" : "=&r"(ccsidr) :);
//   //   printf("ccsidr: %x\n", ccsidr);
//   associativity = ((ccsidr >> ccsidr_assoc_shift) & ccsidr_assoc_mask) + 1;
//   num_sets = ((ccsidr >> ccsidr_nsets_shift) & ccsidr_nests_mask) + 1;
//   //   printf("assoc: %d, nsets: %d\n", associativity, num_sets);

//   assoc_shift = 0;
//   ccsidr = associativity - 1;
//   while (ccsidr != 0) {
//     ccsidr = (ccsidr >> 1);
//     assoc_shift += 1;
//   }
//   assoc_shift = 32 - assoc_shift;
//   //   printf("assoc shift: %d\n", assoc_shift);

//   ccsidr = num_sets - 1;
//   index_mask = 0;
//   while (ccsidr != 0) {
//     ccsidr = (ccsidr >> 1);
//     index_mask += 1;
//   }
//   index_mask = index_mask + 6;
//   index_mask = (1 << index_mask);
//   index_mask = (index_mask - 1) & (~0x3F);
//   //   printf("index mask: %x\n", index_mask);
// }

// static void dc_csw(uint64_t addr) {
//   for (uint64_t way = 0; way < associativity; way++) {
//     uint64_t sw = (addr & index_mask);
//     sw |= (way << assoc_shift);
//     asm volatile("dc csw, %x0" ::"r"(sw));
//   }
// }

// static void dc_cisw(uint64_t addr) {
//   for (uint64_t way = 0; way < associativity; way++) {
//     uint64_t sw = (addr & index_mask);
//     sw |= (way << assoc_shift);
//     asm volatile("dc cisw, %x0" ::"r"(sw));
//   }
// }

void xmain() { mango_core_main_func(xrt_get_core_id()); }