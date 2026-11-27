#include "serial.h"

#define COM1 0x3F8u

static inline void outb(uint16_t port, uint8_t value)
{
    __asm__ volatile ("outb %0, %1" : : "a"(value), "Nd"(port));
}

static void serial_putc(char value)
{
    outb(COM1, (uint8_t)value);
}

void serial_init(void)
{
    outb(COM1 + 1u, 0x00u);
    outb(COM1 + 3u, 0x80u);
    outb(COM1 + 0u, 0x01u);
    outb(COM1 + 1u, 0x00u);
    outb(COM1 + 3u, 0x03u);
    outb(COM1 + 2u, 0xC7u);
    outb(COM1 + 4u, 0x0Bu);
}

void serial_write(const char *value)
{
    while (*value != '\0') {
        if (*value == '\n')
            serial_putc('\r');
        serial_putc(*value++);
    }
}

void serial_write_hex32(uint32_t value)
{
    static const char digits[] = "0123456789ABCDEF";
    serial_write("0x");
    for (int shift = 28; shift >= 0; shift -= 4)
        serial_putc(digits[(value >> (unsigned)shift) & 0x0Fu]);
}

void serial_write_hex64(uint64_t value)
{
    static const char digits[] = "0123456789ABCDEF";
    serial_write("0x");
    for (int shift = 60; shift >= 0; shift -= 4)
        serial_putc(digits[(value >> (unsigned)shift) & 0x0Fu]);
}
