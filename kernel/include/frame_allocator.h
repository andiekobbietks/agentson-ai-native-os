#ifndef AGENTSON_FRAME_ALLOCATOR_H
#define AGENTSON_FRAME_ALLOCATOR_H

#include <stdbool.h>
#include <stdint.h>
#include "multiboot2.h"

#define FRAME_ALLOCATOR_PAGE_SIZE 4096u
#define FRAME_ALLOCATOR_PHYSICAL_LIMIT (1024ull * 1024ull * 1024ull)

bool frame_allocator_init(
    const struct multiboot2_memory_map *map,
    uint64_t kernel_start,
    uint64_t kernel_end,
    uint64_t boot_info_start,
    uint64_t boot_info_end);

uint64_t frame_alloc(void);
bool frame_free(uint64_t physical_address);
uint64_t frame_allocator_free_count(void);

#endif
