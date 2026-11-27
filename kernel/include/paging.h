#ifndef AGENTSON_PAGING_H
#define AGENTSON_PAGING_H

#include <stdbool.h>
#include <stdint.h>

#define PAGING_PAGE_SIZE 4096u
#define PAGING_PRESENT 0x001ull
#define PAGING_WRITABLE 0x002ull
#define PAGING_USER 0x004ull

bool paging_init(uint64_t pml4_physical);
bool paging_map_page(uint64_t virtual_address, uint64_t physical_address,
                     uint64_t flags);
bool paging_unmap_page(uint64_t virtual_address);
bool paging_translate(uint64_t virtual_address, uint64_t *physical_address);

#endif
