#include <stdint.h>
#include "frame_allocator.h"
#include "idt.h"
#include "multiboot2.h"
#include "paging.h"
#include "serial.h"
#include "timer.h"

#define MULTIBOOT2_BOOT_MAGIC 0x36D76289u
#define MAX_BOOTINFO_BYTES (1024u * 1024u)
#define IDENTITY_MAP_LIMIT (1024u * 1024u * 1024u)
#define EXPECTED_UNMAPPED_ADDRESS 0x80000000ull

extern uint8_t __kernel_start[];
extern uint8_t __kernel_end[];
extern uint8_t pml4[];

static __attribute__((noreturn)) void stop_with_error(const char *message)
{
    serial_write("BOOT_ERROR: ");
    serial_write(message);
    serial_write("\n");
    for (;;)
        __asm__ volatile ("cli; hlt");
}

__attribute__((noreturn))
void kernel_main(uint32_t boot_magic, uint32_t boot_info_address)
{
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

    if (!paging_init((uint64_t)(uintptr_t)pml4))
        stop_with_error("page-table manager initialisation failed");

    const uint64_t first_frame = frame_alloc();
    const uint64_t second_frame = frame_alloc();
    if (first_frame == 0u || second_frame == 0u ||
        first_frame == second_frame ||
        (first_frame & 0xFFFu) != 0u ||
        (second_frame & 0xFFFu) != 0u)
        stop_with_error("physical frame allocation test failed");

    const uint64_t high_virtual = 0x40000000ull;
    const uint64_t split_virtual = 0x20000000ull;

    if (!paging_map_page(high_virtual, second_frame, PAGING_WRITABLE) ||
        paging_map_page(high_virtual, second_frame, PAGING_WRITABLE))
        stop_with_error("new page-table branch or duplicate-map check failed");

    if (!paging_unmap_page(split_virtual) ||
        !paging_map_page(split_virtual, first_frame, PAGING_WRITABLE))
        stop_with_error("huge-page split or remapping failed");

    volatile uint64_t *high_mapping =
        (volatile uint64_t *)(uintptr_t)high_virtual;
    volatile uint64_t *split_mapping =
        (volatile uint64_t *)(uintptr_t)split_virtual;
    *high_mapping = 0xA63E50A110C0FFEEull;
    *split_mapping = 0xB007B007C0DEC0DEull;

    uint64_t translated = 0u;
    if (*high_mapping != 0xA63E50A110C0FFEEull ||
        *split_mapping != 0xB007B007C0DEC0DEull ||
        !paging_translate(high_virtual, &translated) ||
        translated != second_frame ||
        !paging_translate(split_virtual, &translated) ||
        translated != first_frame ||
        paging_map_page(high_virtual + 1u, second_frame, PAGING_WRITABLE) ||
        paging_map_page(0x50000000ull, IDENTITY_MAP_LIMIT, PAGING_WRITABLE))
        stop_with_error("page-table translation or alignment check failed");

    if (!paging_unmap_page(high_virtual) ||
        !paging_unmap_page(split_virtual) ||
        paging_translate(high_virtual, &translated) ||
        !frame_free(first_frame) || frame_free(first_frame) ||
        !frame_free(second_frame))
        stop_with_error("page-table unmap or frame release failed");

    serial_write("FRAME_ALLOC: valid\n");
    serial_write("PAGING: valid\n");
    serial_write("FREE_FRAMES: ");
    serial_write_hex64(frame_allocator_free_count());
    serial_write("\n");

    idt_init();
    serial_write("IDT: valid\n");

    timer_init(100u);
    while (timer_ticks() < 3u)
        __asm__ volatile ("hlt");
    timer_stop();
    serial_write("TIMER: valid\n");
    serial_write("TIMER_TICKS: ");
    serial_write_hex64(timer_ticks());
    serial_write("\n");

    serial_write("BOOT_OK: agentson-x86_64-timer-idt-exception\n");

    /* A deliberate supervisor read from an unmapped canonical address. */
    volatile uint64_t fault_value =
        *(volatile uint64_t *)(uintptr_t)EXPECTED_UNMAPPED_ADDRESS;
    (void)fault_value;
    stop_with_error("expected page fault did not occur");
}
