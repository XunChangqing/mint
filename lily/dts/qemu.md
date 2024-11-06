# qemu for numa
virt_4die_8c.dts

```sh
./qemu-system-aarch64 -M virt,secure=true,virtualization=true -cpu cortex-a76 -smp cpus=8 -m size=4096M -machine hmat=on -object memory-backend-ram,id=mem0,size=1024M -object memory-backend-ram,id=mem1,size=1024M -object memory-backend-ram,id=mem2,size=1024M -object memory-backend-ram,id=mem3,size=1024M -numa node,memdev=mem0,cpus=0-1,nodeid=0,initiator=0 -numa node,memdev=mem1,cpus=2-3,nodeid=1,initiator=1 -numa node,memdev=mem2,cpus=4-5,nodeid=2,initiator=2 -numa node,memdev=mem3,cpus=6-7,nodeid=3,initiator=3 -nographic -kernel /home/xuncq/stiwork/mint/lily/memory_bandwidth/build/debug/membw.uimage
```

# qemu with pcie switch and nvme
virt_4c_nvme.dts

create an image file for the nvme drive
```sh
./qemu-img create nvme_disk.img 2G
```

virtual machine, 4 cores, pcie switch, nvme
```sh
./qemu-system-aarch64 -machine virt,secure=true,virtualization=true -cpu cortex-a76 -smp cpus=4 -m 2048M -drive file=nvme_disk.img,if=none,id=nvm,format=raw -device x3130-upstream,id=upstream_port1,bus=pcie.0 -device xio3130-downstream,id=downstream_port1,bus=upstream_port1 -device nvme,serial=deadbeef,drive=nvm,bus=downstream_port1  -nographic -kernel /home/xuncq/stiwork/mint/lily/pci_bringup/build/debug/pci_bringup.uimage
```