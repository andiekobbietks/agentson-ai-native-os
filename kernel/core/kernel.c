#include <stdint.h>
#include "frame_allocator.h"
#include "multiboot2.h"
#include "paging.h"

#define COM1 0x3F8u
#define QEMU_EXIT_PORT 0xF4u
#define MULTIBOOT2_BOOT_MAGIC 0x36D76289u
#define MAX_BOOTINFO_BYTES (1024u * 1024u)
#define IDENTITY_MAP_LIMIT (1024u * 1024u * 1024u)

extern uint8_t __kernel_start[];
extern uint8_t __kernel_end[];
extern uint8_t pml4[];

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
static void serial_write_hex32(uint32_t value) {
    static const char digits[] = "0123456789ABCDEF";
    serial_write("0x");
    for (int shift = 28; shift >= 0; shift -= 4)
        serial_putc(digits[(value >> (unsigned)shift) & 0x0Fu]);
}
static void serial_write_hex64(uint64_t value) {
    static const char digits[] = "0123456789ABCDEF";
    serial_write("0x");
    for (int shift = 60; shift >= 0; shift -= 4)
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
        serial_write("boot_magic=");
        serial_write_hex32(boot_magic);
        serial_write("\n");
        stop_with_error("invalid Multiboot2 magic");
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
    serial_write("BOOTINFO_BYTES: ");
    serial_write_hex32(total_size);
    serial_write("\n");

    struct multiboot2_memory_map memory_map;
    if (!multiboot2_parse_memory_map((const void *)(uintptr_t)boot_info_address,
                                     total_size, &memory_map))
        stop_with_error("invalid or missing Multiboot2 memory map");

    serial_write("MULTIBOOT2_MEMORY_MAP: valid\n");
    serial_write("MEMORY_MAP_ENTRIES: ");
    serial_write_hex32(memory_map.entry_count);
    serial_write("\n");

    const uint64_t boot_info_end = (uint64_t)boot_info_address + total_size;
    if (!frame_allocator_init(&memory_map,
                              (uint64_t)(uintptr_t)__kernel_start,
                              (uint64_t)(uintptr_t)__kernel_end,
                              boot_info_address, boot_info_end))
        stop_with_error("physical frame allocator initialisation failed");

    const uint64_t first_frame = frame_alloc();
    const uint64_t second_frame = frame_alloc();
    if (first_frame == 0u || second_frame == 0u ||
        first_frame == second_frame ||
        (first_frame & 0xFFFu) != 0u ||
        (second_frame & 0xFFFu) != 0u)
        stop_with_error("physical frame allocation test failed");
    if (!frame_free(first_frame) || frame_free(first_frame) ||
        !frame_free(second_frame))
        stop_with_error("physical frame release test failed");

    serial_write("FRAME_ALLOC: valid\n");
    serial_write("FREE_FRAMES: ");
    serial_write_hex64(frame_allocator_free_count());
    serial_write("\n");
    serial_write("BOOT_OK: agentson-x86_64-memory-map-frame-allocator\n");
    qemu_success_exit();
}
