#include "of_fdt.h"

#include <ivy/halt_code.h>
#include <ivy/xrt.h>

#include "ivy_dt.h"
#include "libfdt/libfdt.h"

#include <linux/types.h>

#define OF_ROOT_NODE_ADDR_CELLS_DEFAULT 1
#define OF_ROOT_NODE_SIZE_CELLS_DEFAULT 1

void *of_fdt;
int dt_root_addr_cells;
int dt_root_size_cells;

/**
 * kbasename - return the last part of a pathname.
 *
 * @path: path to extract the filename from.
 */
static inline const char *kbasename(const char *path) {
  const char *tail = strrchr(path, '/');
  return tail ? tail + 1 : path;
}

/**
 * of_scan_flat_dt - scan flattened tree blob and call callback on each.
 * @it: callback function
 * @data: context data pointer
 *
 * This function is used to scan the flattened device-tree, it is
 * used to extract the memory information at boot before we can
 * unflatten the tree
 */
int of_scan_flat_dt(int (*it)(unsigned long node, const char *uname, int depth,
                              void *data),
                    void *data) {
  const void *blob = of_fdt;
  const char *pathp;
  int offset, rc = 0, depth = -1;

  if (!blob) return 0;

  for (offset = fdt_next_node(blob, -1, &depth);
       offset >= 0 && depth >= 0 && !rc;
       offset = fdt_next_node(blob, offset, &depth)) {
    pathp = fdt_get_name(blob, offset, NULL);
    if (*pathp == '/') pathp = kbasename(pathp);
    rc = it(offset, pathp, depth, data);
  }
  return rc;
}

/**
 * of_get_flat_dt_prop - Given a node in the flat blob, return the property ptr
 *
 * This function can be used within scan_flattened_dt callback to get
 * access to properties
 */
const void *of_get_flat_dt_prop(unsigned long node, const char *name,
                                int *size) {
  return fdt_getprop(of_fdt, node, name, size);
}

/**
 * early_init_dt_scan_root - fetch the top level address and size cells
 */
int dt_scan_root(unsigned long node, const char *uname, int depth, void *data) {
  const fdt32_t *prop;

  if (depth != 0) return 0;

  dt_root_size_cells = OF_ROOT_NODE_SIZE_CELLS_DEFAULT;
  dt_root_addr_cells = OF_ROOT_NODE_ADDR_CELLS_DEFAULT;

  prop = of_get_flat_dt_prop(node, "#size-cells", NULL);
  if (prop) dt_root_size_cells = fdt32_to_cpu(*prop);

  prop = of_get_flat_dt_prop(node, "#address-cells", NULL);
  if (prop) dt_root_addr_cells = fdt32_to_cpu(*prop);

  // 停止
  return 1;
}

/* Helper to read a big number; size is in cells (not bytes) */
static inline uint64_t of_read_number(const fdt32_t *cell, int size) {
  uint64_t r = 0;
  while (size--) r = (r << 32) | fdt32_to_cpu(*(cell++));
  return r;
}

uint64_t dt_mem_next_cell(int s, const fdt32_t **cellp) {
  const fdt32_t *p = *cellp;

  *cellp = p + s;
  return of_read_number(p, s);
}

bool memories_check[IVY_DT_NUM_MEMORY] = {false};

/**
 * dt_scan_memory - Look for and parse memory nodes
 */
int dt_scan_memory(unsigned long node, const char *uname, int depth,
                   void *data) {
  const char *type = of_get_flat_dt_prop(node, "device_type", NULL);
  const fdt32_t *reg, *endp;
  int l;
  //   bool hotpluggable;

  /* We are scanning "memory" nodes only */
  if (type == NULL || strcmp(type, "memory") != 0) return 0;

  reg = of_get_flat_dt_prop(node, "linux,usable-memory", &l);
  if (reg == NULL) reg = of_get_flat_dt_prop(node, "reg", &l);
  if (reg == NULL) return 0;

  endp = reg + (l / sizeof(fdt32_t));
  //   hotpluggable = of_get_flat_dt_prop(node, "hotpluggable", NULL);

  //   pr_debug("memory scan node %s, reg size %d,\n", uname, l);

  while ((endp - reg) >= (dt_root_addr_cells + dt_root_size_cells)) {
    uint64_t base, size;

    base = dt_mem_next_cell(dt_root_addr_cells, &reg);
    size = dt_mem_next_cell(dt_root_size_cells, &reg);

    if (size == 0) continue;

    for (int i = 0; i < IVY_DT_NUM_MEMORY; i++) {
      if (ivy_dt_memories[i].start == base && ivy_dt_memories[i].size == size) {
        memories_check[i] = true;
        break;
      }
    }
  }

  return 0;
}

bool cpu_check[IVY_DT_NR_CPUS] = {false};

int dt_cpu_addr_cells;
int dt_cpu_size_cells;

int dt_scan_cpus(unsigned long node, const char *uname, int depth, void *data) {
  const fdt32_t *prop;
  dt_cpu_addr_cells = dt_root_addr_cells;
  dt_cpu_size_cells = dt_root_size_cells;

  if (strcmp(uname, "cpus") != 0) return 0;

  prop = of_get_flat_dt_prop(node, "#size-cells", NULL);
  if (prop) dt_cpu_size_cells = fdt32_to_cpu(*prop);

  prop = of_get_flat_dt_prop(node, "#address-cells", NULL);
  if (prop) dt_cpu_addr_cells = fdt32_to_cpu(*prop);

  return 1;
}

int dt_scan_cpu(unsigned long node, const char *uname, int depth, void *data) {
  const char *type = of_get_flat_dt_prop(node, "device_type", NULL);
  const fdt32_t *reg, *endp;
  int l;
  //   bool hotpluggable;

  /* We are scanning "memory" nodes only */
  if (type == NULL || strcmp(type, "cpu") != 0) return 0;

  reg = of_get_flat_dt_prop(node, "reg", &l);
  if (reg == NULL) return 0;

  uint64_t cpu_id = of_read_number(reg, dt_cpu_addr_cells);

  for (int i = 0; i < IVY_DT_NR_CPUS; i++) {
    if (cpu_id == ivy_dt_cpu_id_map[i]) {
      cpu_check[i] = true;
      break;
    }
  }

  return 0;
}

int fdt_check(void *fdt) {
  if (fdt == NULL) {
    return 0;
  }

  int ec = 0;
  of_fdt = fdt;
  ec = fdt_check_header(fdt);
  if (ec) return ec;

  // 初始化root的地址和大小的cell数量
  of_scan_flat_dt(dt_scan_root, NULL);

  // 遍历所有存储段
  of_scan_flat_dt(dt_scan_memory, NULL);

  // 检查是否所有存储段都存在
  for (int i = 0; i < IVY_DT_NUM_MEMORY; i++) {
    if (memories_check[i] == false) {
      return -1;
    }
  }

  // 获取cpu节点的地址和大小的cell数量
  of_scan_flat_dt(dt_scan_cpus, NULL);

  // 遍历所有cpu节点
  of_scan_flat_dt(dt_scan_cpu, NULL);

  // 检查是否所有cpu节点在设备树中都存在
  for (int i = 0; i < IVY_DT_NR_CPUS; i++) {
    if (cpu_check[i] == false) {
      return -1;
    }
  }

  return 0;
}

//   return 0;
// }