#ifndef AGENTSON_MULTIBOOT2_H
#define AGENTSON_MULTIBOOT2_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define MULTIBOOT2_TAG_END 0u
#define MULTIBOOT2_TAG_MEMORY_MAP 6u
#define MULTIBOOT2_MEMORY_AVAILABLE 1u
#define MULTIBOOT2_MEMORY_MAP_ENTRY_MIN_SIZE 24u

struct multiboot2_memory_map {
    const uint8_t *entries;
    uint32_t entry_count;
    uint32_t entry_size;
};

struct multiboot2_memory_region {
    uint64_t base;
    uint64_t length;
    uint32_t type;
};

bool multiboot2_parse_memory_map(
    const void *boot_info,
    size_t mapped_bytes,
    struct multiboot2_memory_map *out_map);

bool multiboot2_memory_map_get(
    const struct multiboot2_memory_map *map,
    uint32_t index,
    struct multiboot2_memory_region *out_region);

#endif
