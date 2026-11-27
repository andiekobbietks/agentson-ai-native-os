#include "paging.h"
#include "frame_allocator.h"

#define PHYSICAL_ADDRESS_MASK 0x000FFFFFFFFFF000ull
#define HUGE_PAGE_ADDRESS_MASK 0x000FFFFFFFE00000ull
#define HUGE_PAGE_SIZE 0x200000ull
#define IDENTITY_LIMIT (1024ull * 1024ull * 1024ull)
#define ENTRY_COUNT 512u
#define FLAG_HUGE 0x080ull
#define FLAG_ALLOWED (PAGING_WRITABLE | PAGING_USER)

static uint64_t *root_table;

static bool is_canonical(uint64_t address)
{
    const uint64_t upper = address >> 48;
    const bool sign = ((address >> 47) & 1u) != 0u;
    return sign ? upper == 0xFFFFu : upper == 0u;
}

static uint64_t *table_from_physical(uint64_t physical)
{
    if ((physical & (PAGING_PAGE_SIZE - 1u)) != 0u ||
        physical >= IDENTITY_LIMIT)
        return NULL;
    return (uint64_t *)(uintptr_t)physical;
}

static uint64_t allocate_table(void)
{
    const uint64_t physical = frame_alloc();
    if (physical == 0u)
        return 0u;

    uint64_t *table = table_from_physical(physical);
    if (table == NULL) {
        (void)frame_free(physical);
        return 0u;
    }

    for (uint32_t i = 0u; i < ENTRY_COUNT; ++i)
        table[i] = 0u;
    return physical;
}

static uint64_t *get_or_create_table(uint64_t *entry, bool user)
{
    if ((*entry & PAGING_PRESENT) == 0u) {
        const uint64_t physical = allocate_table();
        if (physical == 0u)
            return NULL;
        *entry = physical | PAGING_PRESENT | PAGING_WRITABLE |
                 (user ? PAGING_USER : 0u);
    } else if ((*entry & FLAG_HUGE) != 0u) {
        return NULL;
    } else if (user) {
        *entry |= PAGING_USER;
    }

    return table_from_physical(*entry & PHYSICAL_ADDRESS_MASK);
}

static bool split_huge_page(uint64_t *entry)
{
    if ((*entry & (PAGING_PRESENT | FLAG_HUGE)) !=
        (PAGING_PRESENT | FLAG_HUGE))
        return false;

    const uint64_t old_entry = *entry;
    const uint64_t huge_base = old_entry & HUGE_PAGE_ADDRESS_MASK;
    const uint64_t inherited_flags =
        old_entry & (PAGING_PRESENT | PAGING_WRITABLE | PAGING_USER);
    const uint64_t table_physical = allocate_table();
    if (table_physical == 0u)
        return false;

    uint64_t *table = table_from_physical(table_physical);
    if (table == NULL)
        return false;

    for (uint32_t i = 0u; i < ENTRY_COUNT; ++i) {
        table[i] = huge_base + (uint64_t)i * PAGING_PAGE_SIZE |
                   inherited_flags;
    }

    *entry = table_physical | inherited_flags;
    return true;
}

static void invalidate_page(uint64_t virtual_address)
{
    __asm__ volatile ("invlpg (%0)" : : "r"(virtual_address) : "memory");
}

bool paging_init(uint64_t pml4_physical)
{
    if ((pml4_physical & (PAGING_PAGE_SIZE - 1u)) != 0u ||
        pml4_physical >= IDENTITY_LIMIT)
        return false;
    root_table = table_from_physical(pml4_physical);
    return root_table != NULL;
}

bool paging_map_page(uint64_t virtual_address, uint64_t physical_address,
                     uint64_t flags)
{
    if (root_table == NULL || !is_canonical(virtual_address) ||
        (virtual_address & (PAGING_PAGE_SIZE - 1u)) != 0u ||
        (physical_address & (PAGING_PAGE_SIZE - 1u)) != 0u ||
        physical_address >= IDENTITY_LIMIT || (flags & ~FLAG_ALLOWED) != 0u)
        return false;

    const bool user = (flags & PAGING_USER) != 0u;
    const uint16_t pml4_index = (uint16_t)((virtual_address >> 39) & 0x1FFu);
    const uint16_t pdpt_index = (uint16_t)((virtual_address >> 30) & 0x1FFu);
    const uint16_t pd_index = (uint16_t)((virtual_address >> 21) & 0x1FFu);
    const uint16_t pt_index = (uint16_t)((virtual_address >> 12) & 0x1FFu);

    uint64_t *pdpt = get_or_create_table(&root_table[pml4_index], user);
    if (pdpt == NULL)
        return false;

    uint64_t *pd = get_or_create_table(&pdpt[pdpt_index], user);
    if (pd == NULL)
        return false;

    if ((pd[pd_index] & FLAG_HUGE) != 0u &&
        !split_huge_page(&pd[pd_index]))
        return false;

    uint64_t *pt = get_or_create_table(&pd[pd_index], user);
    if (pt == NULL || (pt[pt_index] & PAGING_PRESENT) != 0u)
        return false;

    pt[pt_index] = physical_address | PAGING_PRESENT | flags;
    invalidate_page(virtual_address);
    return true;
}

bool paging_unmap_page(uint64_t virtual_address)
{
    if (root_table == NULL || !is_canonical(virtual_address) ||
        (virtual_address & (PAGING_PAGE_SIZE - 1u)) != 0u)
        return false;

    const uint16_t pml4_index = (uint16_t)((virtual_address >> 39) & 0x1FFu);
    const uint16_t pdpt_index = (uint16_t)((virtual_address >> 30) & 0x1FFu);
    const uint16_t pd_index = (uint16_t)((virtual_address >> 21) & 0x1FFu);
    const uint16_t pt_index = (uint16_t)((virtual_address >> 12) & 0x1FFu);

    if ((root_table[pml4_index] & PAGING_PRESENT) == 0u)
        return false;
    uint64_t *pdpt = table_from_physical(
        root_table[pml4_index] & PHYSICAL_ADDRESS_MASK);
    if (pdpt == NULL || (pdpt[pdpt_index] & PAGING_PRESENT) == 0u)
        return false;
    uint64_t *pd = table_from_physical(
        pdpt[pdpt_index] & PHYSICAL_ADDRESS_MASK);
    if (pd == NULL || (pd[pd_index] & PAGING_PRESENT) == 0u)
        return false;

    if ((pd[pd_index] & FLAG_HUGE) != 0u &&
        !split_huge_page(&pd[pd_index]))
        return false;

    uint64_t *pt = table_from_physical(
        pd[pd_index] & PHYSICAL_ADDRESS_MASK);
    if (pt == NULL || (pt[pt_index] & PAGING_PRESENT) == 0u)
        return false;

    pt[pt_index] = 0u;
    invalidate_page(virtual_address);
    return true;
}

bool paging_translate(uint64_t virtual_address, uint64_t *physical_address)
{
    if (root_table == NULL || physical_address == NULL ||
        !is_canonical(virtual_address))
        return false;

    const uint16_t pml4_index = (uint16_t)((virtual_address >> 39) & 0x1FFu);
    const uint16_t pdpt_index = (uint16_t)((virtual_address >> 30) & 0x1FFu);
    const uint16_t pd_index = (uint16_t)((virtual_address >> 21) & 0x1FFu);
    const uint16_t pt_index = (uint16_t)((virtual_address >> 12) & 0x1FFu);

    if ((root_table[pml4_index] & PAGING_PRESENT) == 0u)
        return false;
    uint64_t *pdpt = table_from_physical(
        root_table[pml4_index] & PHYSICAL_ADDRESS_MASK);
    if (pdpt == NULL || (pdpt[pdpt_index] & PAGING_PRESENT) == 0u)
        return false;
    uint64_t *pd = table_from_physical(
        pdpt[pdpt_index] & PHYSICAL_ADDRESS_MASK);
    if (pd == NULL || (pd[pd_index] & PAGING_PRESENT) == 0u)
        return false;

    if ((pd[pd_index] & FLAG_HUGE) != 0u) {
        *physical_address =
            (pd[pd_index] & HUGE_PAGE_ADDRESS_MASK) |
            (virtual_address & (HUGE_PAGE_SIZE - 1u));
        return true;
    }

    uint64_t *pt = table_from_physical(
        pd[pd_index] & PHYSICAL_ADDRESS_MASK);
    if (pt == NULL || (pt[pt_index] & PAGING_PRESENT) == 0u)
        return false;

    *physical_address =
        (pt[pt_index] & PHYSICAL_ADDRESS_MASK) |
        (virtual_address & (PAGING_PAGE_SIZE - 1u));
    return true;
}
