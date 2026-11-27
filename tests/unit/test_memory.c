#include "frame_allocator.h"
#include "multiboot2.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static void put_u32(uint8_t *p, uint32_t value)
{
    p[0] = (uint8_t)value;
    p[1] = (uint8_t)(value >> 8);
    p[2] = (uint8_t)(value >> 16);
    p[3] = (uint8_t)(value >> 24);
}

static void put_u64(uint8_t *p, uint64_t value)
{
    put_u32(p, (uint32_t)value);
    put_u32(p + 4u, (uint32_t)(value >> 32));
}

static void put_entry(uint8_t *p, uint64_t base, uint64_t length,
                      uint32_t type)
{
    put_u64(p, base);
    put_u64(p + 8u, length);
    put_u32(p + 16u, type);
    put_u32(p + 20u, 0u);
}

static size_t make_valid_blob(uint8_t *blob, size_t capacity)
{
    const uint32_t entry_size = 24u;
    const uint32_t entry_count = 3u;
    const uint32_t mmap_tag_size = 16u + entry_size * entry_count;
    const size_t end_tag_offset = 8u + mmap_tag_size;
    const size_t total_size = end_tag_offset + 8u;

    assert(capacity >= total_size);
    memset(blob, 0, capacity);
    put_u32(blob, (uint32_t)total_size);
    put_u32(blob + 4u, 0u);

    put_u32(blob + 8u, MULTIBOOT2_TAG_MEMORY_MAP);
    put_u32(blob + 12u, mmap_tag_size);
    put_u32(blob + 16u, entry_size);
    put_u32(blob + 20u, 0u);
    put_entry(blob + 24u, 0x00100000ull, 0x01000000ull,
              MULTIBOOT2_MEMORY_AVAILABLE);
    put_entry(blob + 48u, 0x00300000ull, 0x00001000ull, 2u);
    put_entry(blob + 72u, 0x04000000ull, 0x00001000ull,
              MULTIBOOT2_MEMORY_AVAILABLE);

    put_u32(blob + end_tag_offset, MULTIBOOT2_TAG_END);
    put_u32(blob + end_tag_offset + 4u, 8u);
    return total_size;
}

static void test_parser_rejects_malformed_input(void)
{
    uint64_t storage[64];
    uint8_t *blob = (uint8_t *)storage;
    struct multiboot2_memory_map map;
    const size_t size = make_valid_blob(blob, sizeof(storage));

    assert(!multiboot2_parse_memory_map(blob, size - 1u, &map));

    put_u32(blob + 16u, 8u); /* entry_size smaller than the ABI minimum */
    assert(!multiboot2_parse_memory_map(blob, size, &map));

    make_valid_blob(blob, sizeof(storage));
    put_u64(blob + 24u, UINT64_MAX - 0x1000ull);
    put_u64(blob + 32u, 0x2000ull); /* base + length overflows */
    assert(!multiboot2_parse_memory_map(blob, size, &map));

    make_valid_blob(blob, sizeof(storage));
    put_u32(blob + size - 8u, 1u); /* no valid end tag */
    assert(!multiboot2_parse_memory_map(blob, size, &map));
}

static void test_frame_allocator_reserves_memory(void)
{
    uint64_t storage[64];
    uint8_t *blob = (uint8_t *)storage;
    struct multiboot2_memory_map map;
    struct multiboot2_memory_region region;
    const size_t size = make_valid_blob(blob, sizeof(storage));

    assert(multiboot2_parse_memory_map(blob, size, &map));
    assert(map.entry_count == 3u);
    assert(multiboot2_memory_map_get(&map, 1u, &region));
    assert(region.base == 0x00300000ull && region.type == 2u);
    assert(!multiboot2_memory_map_get(&map, 3u, &region));

    assert(frame_allocator_init(&map, 0x00100000ull, 0x00200000ull,
                                0x00008000ull, 0x00009000ull));
    assert(frame_allocator_free_count() > 0u);

    const uint64_t first = frame_alloc();
    const uint64_t second = frame_alloc();
    assert(first != 0u && second != 0u && first != second);
    assert((first & 0xFFFu) == 0u && (second & 0xFFFu) == 0u);
    assert(first >= 0x00200000ull);
    assert(first != 0x00300000ull && second != 0x00300000ull);
    assert(frame_free(first));
    assert(!frame_free(first)); /* double free */
    assert(!frame_free(0x00300000ull)); /* firmware-reserved frame */
    assert(!frame_free(0x00200001ull)); /* unaligned address */
    assert(frame_free(second));
}

int main(void)
{
    test_parser_rejects_malformed_input();
    test_frame_allocator_reserves_memory();
    puts("PASS: Multiboot2 parser and physical-frame allocator tests.");
    return 0;
}
