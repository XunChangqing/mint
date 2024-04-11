# reference manuals
* armv8 archtecture reference manual
* assembly reference

If you are using the ARM assembler, please refer to https://developer.arm.com/documentation/dui0801/g .
If you prefer the GNU assembler, pleaser refer to 
https://www.gnu.org/manual/ -> https://sourceware.org/binutils/docs/ -> https://sourceware.org/binutils/docs/as.html .
Do not use https://ftp.gnu.org/old-gnu/Manuals/gas-2.9.1/html_chapter/as_toc.html, as it is incomplete.
https://sourceware.org/binutils/docs/as.html#AArch64_002dDependent lists the AArch64 dependent features
including options, opcodeds, etc.

# difference between armasm and gas
There are three pseudo opcodes in armasm: ADRL, MOVL, and LDR pseudo-instruction.
However, only the ldr pseudo-instruction is supported in gas.

# ADRL
The assembler converts an ADRL rn,label pseudo-instruction by generating:
* Two data processing instructions that load the address, if it is in range.
* An error message if the address cannot be constructed in two instructions.

# MOVL
MOVL generates either two or four instructions. If a Wd register is specified, MOVL generates a MOV, MOVK pair. If an Xd register is specified, MOVL generates a MOV followed by three MOVK instructions. If the assembler can load the register using a single MOV instruction, it additionally generates either one or three NOPs.

# methods to load a large constant into a register
* using ldr pseudo-opcodes
  
The assembler will place the large constant in the nearest literal pool, and generate a pc-relative
ldr to read the constant into the register.

The assembler uses literal pools to store some constant data in code sections. You can use the LTORG directive to ensure a literal pool is within range.

The assembler places a literal pool at the end of each section. The end of a section is defined either by the END directive at the end of the assembly or by the AREA directive at the start of the following section. The END directive at the end of an included file does not signal the end of a section.

* using multiple mov instructions in gas

