#include "multiboot2.h"

#define MULTIBOOT2_INFO_HEADER_SIZE 8u
#define MULTIBOOT2_TAG_HEADER_SIZE 8u
#define MULTIBOOT2_MEMORY_MAP_TAG_HEADER_SIZE 16u

static uint32_t read_u32(const uint8_t *p)
{
    return (uint32_t)p[0] |
           ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) |
           ((uint32_t)p[3] << 24);
}

static uint64_t read_u64(const uint8_t *p)
{
    return (uint64_t)read_u32(p) |
           ((uint64_t)read_u32(p + 4u) << 32);
}

bool multiboot2_parse_memory_map(
    const void *boot_info,
    size_t mapped_bytes,
    struct multiboot2_memory_map *out_map)
{
    if (boot_info == NULL || out_map == NULL ||
        mapped_bytes < MULTIBOOT2_INFO_HEADER_SIZE + MULTIBOOT2_TAG_HEADER_SIZE)
        return false;

    out_map->entries = NULL;
    out_map->entry_count = 0u;
    out_map->entry_size = 0u;

    const uint8_t *bytes = (const uint8_t *)boot_info;
    const uint32_t total_size = read_u32(bytes);
    const uint32_t reserved = read_u32(bytes + 4u);

    if (reserved != 0u || total_size < 16u ||
        (total_size & 7u) != 0u || (size_t)total_size > mapped_bytes)
        return false;

    size_t offset = MULTIBOOT2_INFO_HEADER_SIZE;
    bool found_memory_map = false;
    bool found_end_tag = false;

    while (offset <= (size_t)total_size - MULTIBOOT2_TAG_HEADER_SIZE) {
        const uint32_t type = read_u32(bytes + offset);
        const uint32_t tag_size = read_u32(bytes + offset + 4u);

        if (tag_size < MULTIBOOT2_TAG_HEADER_SIZE ||
            (size_t)tag_size > (size_t)total_size - offset)
            return false;

        if (type == MULTIBOOT2_TAG_END) {
            if (tag_size != MULTIBOOT2_TAG_HEADER_SIZE ||
                offset + MULTIBOOT2_TAG_HEADER_SIZE != (size_t)total_size)
                return false;
            found_end_tag = true;
            break;
        }

        if (type == MULTIBOOT2_TAG_MEMORY_MAP) {
            if (found_memory_map ||
                tag_size < MULTIBOOT2_MEMORY_MAP_TAG_HEADER_SIZE)
                return false;

            const uint32_t entry_size = read_u32(bytes + offset + 8u);
            const uint32_t entry_version = read_u32(bytes + offset + 12u);
            const uint32_t entries_bytes =
                tag_size - MULTIBOOT2_MEMORY_MAP_TAG_HEADER_SIZE;

            if (entry_size < MULTIBOOT2_MEMORY_MAP_ENTRY_MIN_SIZE ||
                entry_version != 0u || entries_bytes % entry_size != 0u)
                return false;

            const uint32_t entry_count = entries_bytes / entry_size;
            const uint8_t *entries =
                bytes + offset + MULTIBOOT2_MEMORY_MAP_TAG_HEADER_SIZE;

            for (uint32_t i = 0u; i < entry_count; ++i) {
                const uint8_t *entry = entries + (size_t)i * entry_size;
                const uint64_t base = read_u64(entry);
                const uint64_t length = read_u64(entry + 8u);
                if (length > UINT64_MAX - base)
                    return false;
            }

            out_map->entries = entries;
            out_map->entry_count = entry_count;
            out_map->entry_size = entry_size;
            found_memory_map = true;
        }

        const size_t aligned_size = ((size_t)tag_size + 7u) & ~(size_t)7u;
        if (aligned_size > (size_t)total_size - offset)
            return false;
        offset += aligned_size;
    }

    return found_memory_map && found_end_tag;
}

bool multiboot2_memory_map_get(
    const struct multiboot2_memory_map *map,
    uint32_t index,
    struct multiboot2_memory_region *out_region)
{
    if (map == NULL || out_region == NULL || map->entries == NULL ||
        map->entry_size < MULTIBOOT2_MEMORY_MAP_ENTRY_MIN_SIZE ||
        index >= map->entry_count)
        return false;

    const uint8_t *entry = map->entries + (size_t)index * map->entry_size;
    out_region->base = read_u64(entry);
    out_region->length = read_u64(entry + 8u);
    out_region->type = read_u32(entry + 16u);
    return out_region->length <= UINT64_MAX - out_region->base;
}
