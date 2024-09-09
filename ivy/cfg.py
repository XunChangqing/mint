import typing
from dataclasses import dataclass
from ivy.kernel import pt

@dataclass
class Config:
    # 没有任何booter，独立运行，一般用于软仿，初始化通过 sv 代码进行
    no_booter: bool = False
    # 页尺寸大小，为空时默认为64KB
    page_size: typing.Optional[int] = None
    linear_mapping_flag: pt.Flag = 0
    # 程序加载地址基地址，
    # 在使用uboot时，一般为在uboot中加载内核镜像的目标地址，例如典型的0x80080000
    # 此处80000为内核要求的TEXT_OFFSET，0x80000000为全部ram的最低地址
    # 在qemu中，如果直接通过 -kernel 指定内核文件，则内核文件的加载位置根据uImage镜像
    # 头部的load地址决定，由于qemu会将简单的环境准备boot代码插入到ram最低位置处，所以
    # 在qemu中一般时最小ram地址+TEXT_OFFSET，即0x80000
    # 统一起来，如果用户不知道，则默认为最小ram地址+0x80000
    load_addr: typing.Optional[int] = None
