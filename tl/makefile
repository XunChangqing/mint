CROSS_COMPILE ?= aarch64-none-elf-
CC := $(CROSS_COMPILE)gcc
LD := $(CROSS_COMPILE)ld.bfd
OBJDUMP := $(CROSS_COMPILE)objdump
OBJCOPY := $(CROSS_COMPILE)objcopy

# c preprocessor flags, .S -> .s, .c -> .o
CPPFLAGS := 
# c compiler flags, .c -> .o
CFLAGS := -O0 -g -std=gnu99 -nostdlib -fno-builtin -ffreestanding -march=armv8-a
# assembler flags, .s -> .o
ASFLAGS :=
LDFLAGS := -Bstatic -pie --no-dynamic-linker
BUILD_DIR = build

OBJS := head.o

all: tl.elf tl.diss tl.image

# builtin.o : test.o
# 	$(LD) -r -o $@ $<
head.o: head.S
	$(CC) $(AFLAGS) -c -o $@ $<

# 使用S作为linker脚本扩展名，并进行预处理，这样允许脚本中使用宏定义
# -P表示仅预处理，-E表示不添加行信息，保证生成的lds是合法的
tl.lds: tl.lds.S
	$(CC) $(CPPFLAGS) -E -P -o $@ $<

tl.elf: $(OBJS) tl.lds
	$(LD) -T tl.lds --no-gc-sections -Bstatic -o tl.elf -Map tl.map head.o

tl.diss: tl.elf
	$(OBJDUMP) -S -d tl.elf > tl.diss

tl.image: tl.elf
	$(OBJCOPY) -O binary -S tl.elf tl.image

clean:
	rm -f tl.lds tl.elf tl.diss tl.image
	rm -f $(OBJS)
