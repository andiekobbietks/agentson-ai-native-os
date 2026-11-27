; AgentSON AI-Native OS: Multiboot2 32-bit entry to x86-64 long mode.
; The bootloader enters in 32-bit protected mode. We establish a small
; identity map for the first 1 GiB, enable long mode, then call C code.
BITS 32
section .multiboot
align 8
mb2_header:
    dd 0xE85250D6
    dd 0
    dd mb2_header_end - mb2_header
    dd -(0xE85250D6 + (mb2_header_end - mb2_header))
    dw 0
    dw 0
    dd 8
mb2_header_end:
section .text
global _start
extern kernel_main
_start:
    cli
    cld
    mov [boot_magic], eax
    mov [boot_info], ebx
    mov esp, stack_top
    mov eax, pdpt
    or eax, 0x03
    mov [pml4], eax
    mov dword [pml4 + 4], 0
    mov eax, pd
    or eax, 0x03
    mov [pdpt], eax
    mov dword [pdpt + 4], 0
    xor edi, edi
.map_pd:
    mov eax, edi
    shl eax, 21
    or eax, 0x83
    mov [pd + edi * 8], eax
    mov dword [pd + edi * 8 + 4], 0
    inc edi
    cmp edi, 512
    jne .map_pd
    mov eax, cr4
    or eax, 1 << 5
    mov cr4, eax
    mov ecx, 0xC0000080
    rdmsr
    or eax, 1 << 8
    wrmsr
    mov eax, pml4
    mov cr3, eax
    mov eax, cr0
    or eax, 1 << 31
    mov cr0, eax
    lgdt [gdt64.pointer]
    jmp 0x08:long_mode_start
BITS 64
long_mode_start:
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov ss, ax
    xor ax, ax
    mov fs, ax
    mov gs, ax
    mov rsp, stack_top
    and rsp, -16
    mov edi, [rel boot_magic]
    mov esi, [rel boot_info]
    call kernel_main
.halt:
    cli
    hlt
    jmp .halt
BITS 32
align 8
gdt64:
    dq 0
    dq 0x00AF9A000000FFFF
    dq 0x00CF92000000FFFF
.pointer:
    dw $ - gdt64 - 1
    dd gdt64
section .bss
alignb 4096
pml4: resb 4096
alignb 4096
pdpt: resb 4096
alignb 4096
pd: resb 4096
alignb 16
boot_magic: resd 1
boot_info: resd 1
alignb 16
stack_bottom: resb 16384
stack_top:
