#ifndef AGENTSON_IDT_H
#define AGENTSON_IDT_H

#include <stddef.h>
#include <stdint.h>

struct exception_frame {
    uint64_t r15;
    uint64_t r14;
    uint64_t r13;
    uint64_t r12;
    uint64_t r11;
    uint64_t r10;
    uint64_t r9;
    uint64_t r8;
    uint64_t rdi;
    uint64_t rsi;
    uint64_t rbp;
    uint64_t rdx;
    uint64_t rcx;
    uint64_t rbx;
    uint64_t rax;
    uint64_t vector;
    uint64_t error_code;
    uint64_t rip;
    uint64_t cs;
    uint64_t rflags;
    uint64_t rsp;
    uint64_t ss;
} __attribute__((packed));

_Static_assert(sizeof(struct exception_frame) == 176u,
               "x86-64 IRETQ frame must contain five hardware return slots");
_Static_assert(offsetof(struct exception_frame, rsp) == 160u,
               "x86-64 IRETQ RSP slot offset mismatch");
_Static_assert(offsetof(struct exception_frame, ss) == 168u,
               "x86-64 IRETQ SS slot offset mismatch");

void idt_init(void);
void exception_dispatch(struct exception_frame *frame)
    __attribute__((noreturn));

#endif
