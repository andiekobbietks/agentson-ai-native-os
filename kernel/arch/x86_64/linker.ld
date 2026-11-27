OUTPUT_FORMAT(elf64-x86-64)
OUTPUT_ARCH(i386:x86-64)
ENTRY(_start)
SECTIONS
{
    . = 1M;
    .multiboot ALIGN(8) : { KEEP(*(.multiboot)) }
    .text ALIGN(4K) : { *(.text*) }
    .rodata ALIGN(4K) : { *(.rodata*) }
    .data ALIGN(4K) : { *(.data*) }
    .bss ALIGN(4K) (NOLOAD) : { *(COMMON) *(.bss*) }
    /DISCARD/ : { *(.eh_frame*) *(.note*) *(.comment*) }
}
ASSERT(_start >= 0x100000, "kernel must be loaded above 1 MiB")
