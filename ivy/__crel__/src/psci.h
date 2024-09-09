#pragma once
#include <stdint.h>

#define PSCI_POWER_STATE_TYPE_STANDBY 0
#define PSCI_POWER_STATE_TYPE_POWER_DOWN 1

enum psci_conduit {
  PSCI_CONDUIT_NONE,
  PSCI_CONDUIT_SMC,
  PSCI_CONDUIT_HVC,
};

enum smccc_version {
  SMCCC_VERSION_1_0,
  SMCCC_VERSION_1_1,
};

void cpu_psci_init(enum psci_conduit);
int psci_cpu_on(uint64_t cpuid, uint64_t entry_point);

// int cpu_psci_cpu_boot(unsigned int cpu);
