#include "frame_allocator.h"

#define FRAME_COUNT (FRAME_ALLOCATOR_PHYSICAL_LIMIT / FRAME_ALLOCATOR_PAGE_SIZE)
#define BITMAP_BYTES (FRAME_COUNT / 8u)
#define LOW_MEMORY_RESERVED (1024ull * 1024ull)

static uint8_t used_bitmap[BITMAP_BYTES];
static uint8_t reserved_bitmap[BITMAP_BYTES];
static uint32_t allocation_hint;

static bool bit_is_set(const uint8_t *bitmap, uint32_t frame)
{
    return (bitmap[frame >> 3] & (uint8_t)(1u << (frame & 7u))) != 0u;
}

static void bit_set(uint8_t *bitmap, uint32_t frame)
{
    bitmap[frame >> 3] |= (uint8_t)(1u << (frame & 7u));
}

static void bit_clear(uint8_t *bitmap, uint32_t frame)
{
    bitmap[frame >> 3] &= (uint8_t)~(uint8_t)(1u << (frame & 7u));
}

static void reserve_frames(uint64_t start, uint64_t end)
{
    if (start >= FRAME_ALLOCATOR_PHYSICAL_LIMIT || end <= start)
        return;
    if (end > FRAME_ALLOCATOR_PHYSICAL_LIMIT)
        end = FRAME_ALLOCATOR_PHYSICAL_LIMIT;

    const uint64_t first = start / FRAME_ALLOCATOR_PAGE_SIZE;
    const uint64_t last =
        (end + FRAME_ALLOCATOR_PAGE_SIZE - 1u) / FRAME_ALLOCATOR_PAGE_SIZE;

    for (uint64_t frame = first; frame < last; ++frame) {
        bit_set(used_bitmap, (uint32_t)frame);
        bit_set(reserved_bitmap, (uint32_t)frame);
    }
}

static void release_usable_frames(uint64_t base, uint64_t length)
{
    if (length == 0u || base >= FRAME_ALLOCATOR_PHYSICAL_LIMIT ||
        length > UINT64_MAX - base)
        return;

    uint64_t end = base + length;
    if (end > FRAME_ALLOCATOR_PHYSICAL_LIMIT)
        end = FRAME_ALLOCATOR_PHYSICAL_LIMIT;

    const uint64_t first =
        (base + FRAME_ALLOCATOR_PAGE_SIZE - 1u) / FRAME_ALLOCATOR_PAGE_SIZE;
    const uint64_t last = end / FRAME_ALLOCATOR_PAGE_SIZE;

    for (uint64_t frame = first; frame < last; ++frame) {
        bit_clear(used_bitmap, (uint32_t)frame);
        bit_clear(reserved_bitmap, (uint32_t)frame);
    }
}

bool frame_allocator_init(
    const struct multiboot2_memory_map *map,
    uint64_t kernel_start,
    uint64_t kernel_end,
    uint64_t boot_info_start,
    uint64_t boot_info_end)
{
    if (map == NULL || map->entries == NULL ||
        kernel_end <= kernel_start || boot_info_end <= boot_info_start)
        return false;

    for (uint32_t i = 0u; i < BITMAP_BYTES; ++i) {
        used_bitmap[i] = 0xFFu;
        reserved_bitmap[i] = 0xFFu;
    }

    /* First make only firmware-reported available frames allocatable. */
    for (uint32_t i = 0u; i < map->entry_count; ++i) {
        struct multiboot2_memory_region region;
        if (!multiboot2_memory_map_get(map, i, &region))
            return false;
        if (region.type == MULTIBOOT2_MEMORY_AVAILABLE)
            release_usable_frames(region.base, region.length);
    }

    /* Reserved and non-available firmware regions always take precedence. */
    for (uint32_t i = 0u; i < map->entry_count; ++i) {
        struct multiboot2_memory_region region;
        if (!multiboot2_memory_map_get(map, i, &region))
            return false;
        if (region.type != MULTIBOOT2_MEMORY_AVAILABLE)
            reserve_frames(region.base, region.base + region.length);
    }

    reserve_frames(0u, LOW_MEMORY_RESERVED);
    reserve_frames(kernel_start, kernel_end);
    reserve_frames(boot_info_start, boot_info_end);
    allocation_hint = (uint32_t)(LOW_MEMORY_RESERVED / FRAME_ALLOCATOR_PAGE_SIZE);
    return true;
}

uint64_t frame_alloc(void)
{
    const uint32_t first = allocation_hint;
    for (uint32_t offset = 0u; offset < FRAME_COUNT; ++offset) {
        const uint32_t frame = (first + offset) % (uint32_t)FRAME_COUNT;
        if (!bit_is_set(used_bitmap, frame)) {
            bit_set(used_bitmap, frame);
            allocation_hint = (frame + 1u) % (uint32_t)FRAME_COUNT;
            return (uint64_t)frame * FRAME_ALLOCATOR_PAGE_SIZE;
        }
    }
    return 0u;
}

bool frame_free(uint64_t physical_address)
{
    if ((physical_address & (FRAME_ALLOCATOR_PAGE_SIZE - 1u)) != 0u ||
        physical_address >= FRAME_ALLOCATOR_PHYSICAL_LIMIT)
        return false;

    const uint32_t frame =
        (uint32_t)(physical_address / FRAME_ALLOCATOR_PAGE_SIZE);
    if (bit_is_set(reserved_bitmap, frame) ||
        !bit_is_set(used_bitmap, frame))
        return false;

    bit_clear(used_bitmap, frame);
    if (frame < allocation_hint)
        allocation_hint = frame;
    return true;
}

uint64_t frame_allocator_free_count(void)
{
    uint64_t count = 0u;
    for (uint32_t frame = 0u; frame < FRAME_COUNT; ++frame) {
        if (!bit_is_set(used_bitmap, frame))
            ++count;
    }
    return count;
}
