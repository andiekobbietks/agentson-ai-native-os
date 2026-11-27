#include "idt.h"

#include <stddef.h>
#include <stdint.h>

struct idt_gate {
    uint16_t offset_low;
    uint16_t selector;
    uint8_t ist;
    uint8_t type_attributes;
    uint16_t offset_middle;
    uint32_t offset_high;
    uint32_t reserved;
} __attribute__((packed));

struct idt_register {
    uint16_t limit;
    uint64_t base;
} __attribute__((packed));

static struct idt_gate idt[256] __attribute__((aligned(16)));
extern void (*isr_stub_table[32])(void);

static void set_gate(uint8_t vector, uintptr_t handler)
{
    idt[vector].offset_low = (uint16_t)(handler & 0xFFFFu);
    idt[vector].selector = 0x08u;
    idt[vector].ist = 0u;
    idt[vector].type_attributes = 0x8Eu;
    idt[vector].offset_middle = (uint16_t)((handler >> 16) & 0xFFFFu);
    idt[vector].offset_high = (uint32_t)(handler >> 32);
    idt[vector].reserved = 0u;
}

void idt_init(void)
{
    for (size_t i = 0u; i < 256u; ++i) {
        idt[i].offset_low = 0u;
        idt[i].selector = 0u;
        idt[i].ist = 0u;
        idt[i].type_attributes = 0u;
        idt[i].offset_middle = 0u;
        idt[i].offset_high = 0u;
        idt[i].reserved = 0u;
    }

    for (uint8_t vector = 0u; vector < 32u; ++vector)
        set_gate(vector, (uintptr_t)isr_stub_table[vector]);

    const struct idt_register idtr = {
        .limit = (uint16_t)(sizeof(idt) - 1u),
        .base = (uint64_t)(uintptr_t)idt,
    };
    __asm__ volatile ("lidt %0" : : "m"(idtr));
}
