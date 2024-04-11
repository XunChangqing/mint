# 静态存储分配的支持
指定代码段起始位置以后，如果激励希望在静态情况下分配使用剩余可用存储空间，则需要知道剩余空间的具体分布，此时由于代码尚未链接，
具体代码会占用多少空间未知，所以无法在静态情况下支持确切的可用存储起始位置。
目前方案是，设定给一个代码段使用的最大尺寸，比如64MB，显然该尺寸可以配置，链接时会检查该尺寸不会越界。
如果激励希望可以扫描所有可用存储空间，则代码结束位置可以在运行时通过链接器变量获得，然后在运行时扫描从
该位置到64MB之间的空间。

# 静态页表内容生成的方式
如果使用python脚本生成页表内容对应的C或是汇编代码，则指向下级页表的表项很难实现，
因为下级页表的地址是一个变量，这个地址对低位和高位取0以后，与属性进行或操作，在C
语言中或是汇编中这样的数组初始化方法是不允许的，例如

```asm
.section .pt_data
.global pgd
// .align PAGE_SHIFT
pgd:
    .quad pud0

.align PAGE_SHIFT
pud0:
    .quad page_table_start
```

其中 .quad pud0 可以直接写地址，但是描述符格式需要低位设置属性，高位也设置属性，
也允许+3，即做加法，由于页表首地址页尺寸对齐，所以低位必然为0，+3可以实现低位
两个bit置1。

方法1，使用汇编代码，通过地址和加法实现，由于地址页对齐，低位为0，同时需要使用
物理地址，则高位必然为0，通过加法，可以实现类似逻辑或操作

方法2，以后如果有更复杂的需求，可以python直接进行静态存储分配，给定页表起始地址
python直接输出二进制页表内容，修改link以后生成的elf文件，增加新的section用于
放置页表数据

# 地址映射，暂时全部地址使用一一映射，否则起始代码段需要特殊处理，目前貌似没有看到有特别的需求

# 关于SP寄存器访问
spsel, sp, sp_el0, sp_el1, sp_el2, sp_el3
按照文档arm trm说明，在spsel为1时，通过mov指令访问sp访问的对应el级别的sp_elx寄存器
从权限上将每个el级别可以通过mov, sub, add等指令访问和使用本级sp
但是如果通过mrs/msr访问sp_elx，则el1及以上才能访问sp_el0，el2及以上才能访问sp_el1。
这貌似不太合理，但是考虑实际应用场景，一般将spsel设置为1，这样保证各级都有自己的栈，因为
一般不同级别不会共用栈，比如用户态程序不会和内核态共用栈，el级别变化时改变使用的栈位置也是
很合理的。
同时高级别有时需要访问低级别的栈位置，比如在发生系统调用时，内核可能需要访问用户态程序的栈
空间，此时可以通过直接访问sp_el0来显式的访问用户程序栈空间，而不需要先修改spsel，然后再
访问sp，然后再改回来。

注：
linux内核将spsel设置为1，并且一般通过sp访问本级栈空间，包括在entry.S中初始化内核栈空间时

特别说明：
在QEMU中，EL1情况下，如果spsel为0，不允许通过msr/mrs访问sp_el0会卡住，这也可以理解，一般使用场景不会
是这样的

# gdb备忘
set disassemble-next-line on
set scheduler-locking on, allow only a single thread to run
thread thread-no, set current thread

# qemu备忘

## aarch64 virt machine secondary cpus halted when reset

```c
    /* If we have an EL3 boot ROM then the assumption is that it will
     * implement PSCI itself, so disable QEMU's internal implementation
     * so it doesn't get in the way. Instead of starting secondary
     * CPUs in PSCI powerdown state we will start them all running and
     * let the boot ROM sort them out.
     * The usual case is that we do use QEMU's PSCI implementation;
     * if the guest has EL2 then we will use SMC as the conduit,
     * and otherwise we will use HVC (for backwards compatibility and
     * because if we're using KVM then we must use HVC).
     */
    if (vms->secure && firmware_loaded) {
        vms->psci_conduit = QEMU_PSCI_CONDUIT_DISABLED;
    } else if (vms->virt) {
        vms->psci_conduit = QEMU_PSCI_CONDUIT_SMC;
    } else {
        vms->psci_conduit = QEMU_PSCI_CONDUIT_HVC;
    }
```
如果需要多个处理核都直接进入elf文件入口点，需要将hw/arm/virt.c文件中该处源码将
vms->psci_conduit强制设置为QEMU_PSCI_CONDUIT_DISABLED，否则qemu会自动插入
psci引导固件，导致除了主核以外其他核都等待psci通知，并且会保留占用部分ram空间

./qemu-system-aarch64 -machine virt,dumpdts=virt.dts -cpu cortex-a57
dtc -I dtb -O dts virt.dtb >> virt.dts

启动两个处理核，加载elf，并将两个处理核pc都设置到入口点地址处
```sh
./qemu-system-aarch64 -d int,mmu,unimp -machine virt -cpu cortex-a76 -smp cpus=2 -m 2048M -device loader,file=/home/xuncq/stiwork/xapp/playground/tt.elf,cpu-num=0 -device loader,addr=0x80080000,cpu-num=1  -nographic -s -S
```

```sh
./qemu-system-aarch64 -d int,mmu,unimp -machine virt,secure=true,virtualization=true -cpu cortex-a76 -smp cpus=2 -m 2048M -device loader,file=/home/xuncq/stiwork/xapp/zoo/simple/build/simple.elf,cpu-num=0 -device loader,addr=0x80080000,cpu-num=1  -nographic
```