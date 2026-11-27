#include <stdint.h>
#define COM1 0x3F8u
#define QEMU_EXIT_PORT 0xF4u
#define MULTIBOOT2_BOOT_MAGIC 0x36D76289u
#define MAX_BOOTINFO_BYTES (1024u * 1024u)
#define IDENTITY_MAP_LIMIT (1024u * 1024u * 1024u)
static inline void outb(uint16_t port, uint8_t value) {
    __asm__ volatile ("outb %0, %1" : : "a"(value), "Nd"(port));
}
static inline void outl(uint16_t port, uint32_t value) {
    __asm__ volatile ("outl %0, %1" : : "a"(value), "Nd"(port));
}
static void serial_init(void) {
    outb(COM1 + 1u, 0x00u); outb(COM1 + 3u, 0x80u);
    outb(COM1 + 0u, 0x01u); outb(COM1 + 1u, 0x00u);
    outb(COM1 + 3u, 0x03u); outb(COM1 + 2u, 0xC7u);
    outb(COM1 + 4u, 0x0Bu);
}
static void serial_putc(char value) { outb(COM1, (uint8_t)value); }
static void serial_write(const char *value) {
    while (*value != '\0') {
        if (*value == '\n') serial_putc('\r');
        serial_putc(*value++);
    }
}
static void serial_write_hex(uint32_t value) {
    static const char digits[] = "0123456789ABCDEF";
    serial_write("0x");
    for (int shift = 28; shift >= 0; shift -= 4)
        serial_putc(digits[(value >> (unsigned)shift) & 0x0Fu]);
}
static __attribute__((noreturn)) void stop_with_error(const char *message) {
    serial_write("BOOT_ERROR: "); serial_write(message); serial_write("\n");
    for (;;) __asm__ volatile ("cli; hlt");
}
static __attribute__((noreturn)) void qemu_success_exit(void) {
    outl(QEMU_EXIT_PORT, 0x10u);
    for (;;) __asm__ volatile ("cli; hlt");
}
__attribute__((noreturn))
void kernel_main(uint32_t boot_magic, uint32_t boot_info_address) {
    serial_init();
    serial_write("\nAgentSON x86_64 kernel\n");
    serial_write("BOOT_STAGE: long_mode_entered\n");
    if (boot_magic != MULTIBOOT2_BOOT_MAGIC) {
        serial_write("boot_magic="); serial_write_hex(boot_magic);
        serial_write("\n"); stop_with_error("invalid Multiboot2 magic");
    }
    if (boot_info_address == 0u ||
        boot_info_address >= IDENTITY_MAP_LIMIT ||
        (boot_info_address & 7u) != 0u)
        stop_with_error("invalid Multiboot2 information pointer");
    const volatile uint32_t *boot_info =
        (const volatile uint32_t *)(uintptr_t)boot_info_address;
    const uint32_t total_size = boot_info[0];
    if (total_size < 16u || total_size > MAX_BOOTINFO_BYTES ||
        (uint64_t)boot_info_address + total_size > IDENTITY_MAP_LIMIT)
        stop_with_error("invalid Multiboot2 information size");
    serial_write("MULTIBOOT2_MAGIC: valid\n");
    serial_write("BOOTINFO_BYTES: "); serial_write_hex(total_size);
    serial_write("\n");
    serial_write("BOOT_OK: agentson-x86_64-multiboot2\n");
    qemu_success_exit();
}
