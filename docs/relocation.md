# relocatable裸机代码设计

## 代码在relocate时会发生什么问题
一般在aarch64生成的代码中，针对全局变量的引用都是使用adrp进行，都是位置无关的代码，但是在需要存储绝对地址时，就会导致
代码在relocate时发生问题。
例如以下的C语言和汇编语言代码都演示了这个问题。
C语言中，指针p需要保存x的地址，并且p是全局变量，需要保存在data段中，即在data段中需要显式保存x符号的绝对地址。
类似的，在汇编语言中，_head_addr符号处需要保存_head符号的地址，同样需要绝对地址。
通过readelf -r看到这两个obj文件里面都有一个需要relocate的符号，类型为ABS，急需要使用对应符号的绝对地址来修改指定
偏移位置。
注意这里编译文件时，不要pic也不需要pie，甚至需要使用-fno-pic和-fno-pie
pic主要用于linux环境下动态共享库的建立

```c
int x=2;
static int *p = &x;
```

```sh
aarch64-none-linux-gnu-gcc -c a.c
```

```sh
aarch64-none-linux-gnu-readelf -r a.o
```

```
Relocation section '.rela.data' at offset 0x1a8 contains 1 entry:
  Offset          Info           Type           Sym. Value    Sym. Name + Addend
000000000000  000900000101 R_AARCH64_ABS64   0000000000000004 x + 0
```

```s
    .text
_head:
    nop
    nop

    .data
_head_addr: .quad _head
```

aarch64-none-linux-gnu-gcc -c b.s

aarch64-none-linux-gnu-readelf -r b.o

Relocation section '.rela.data' at offset 0x110 contains 1 entry:
  Offset          Info           Type           Sym. Value    Sym. Name + Addend
000000000000  000100000101 R_AARCH64_ABS64   0000000000000000 .text + 0

最后通过ld把文件链接起来，需要注意的是要增加-pie选项。
链接以后，同样通过reald -r查看，可以看到，有两个rela项，但是类型都是relative，含义是需要使用base+offset+addended
来修改对应offset位置。

## 解决方法
通过objdump可以看到，这两个offset位置分别对应于head_addr和p的保存位置，两者的addend分别为0和40，意思是如果
代码发生relocate需要修改这两处，以p为例。
如果代码被放到0x80000000处，那么0x80000048处的值需要修改为0x80000000+0x40，即为此时x的地址正确位置。

```lds
SECTIONS
{
 .text :
 {
    *(.text*)
 }
 .data : {
    *(.data*)
 }
}
```

aarch64-none-linux-gnu-ld -T t.lds -pie b.o a.o

aarch64-none-linux-gnu-readelf -r a.out

Relocation section '.rela.dyn' at offset 0x10008 contains 2 entries:
  Offset          Info           Type           Sym. Value    Sym. Name + Addend
000000000038  000000000403 R_AARCH64_RELATIV                    0
000000000048  000000000403 R_AARCH64_RELATIV                    40

aarch64-none-linux-gnu-objdump -D a.out

```
Disassembly of section .text:

0000000000000000 <_head>:
   0:	d503201f 	nop
   4:	d503201f 	nop

Disassembly of section .rela.dyn:

0000000000000008 <.rela.dyn>:
   8:	00000038 	.inst	0x00000038 ; undefined
   c:	00000000 	.inst	0x00000000 ; undefined
  10:	00000403 	.inst	0x00000403 ; undefined
	...
  20:	00000048 	.inst	0x00000048 ; undefined
  24:	00000000 	.inst	0x00000000 ; undefined
  28:	00000403 	.inst	0x00000403 ; undefined
  2c:	00000000 	.inst	0x00000000 ; undefined
  30:	00000040 	.inst	0x00000040 ; undefined
  34:	00000000 	.inst	0x00000000 ; undefined

Disassembly of section .data:

0000000000000038 <head_addr>:
	...

0000000000000040 <x>:
  40:	00000002 	.inst	0x00000002 ; undefined
  44:	00000000 	.inst	0x00000000 ; undefined

0000000000000048 <p>:
  48:	00000040 	.inst	0x00000040 ; undefined
  4c:	00000000 	.inst	0x00000000 ; undefined
```
