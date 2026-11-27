# ADR 0011: Bounded bitmap frame allocator for the initial 1 GiB map

- **Status:** Accepted for initial kernel milestones
- **Date:** 2026-11-27

## Context

The kernel needs a small physical-frame allocator before page-table management and higher-level memory services can be built. The initial boot page tables identity-map only the first 1 GiB. Allocating physical addresses outside that mapped range would create unsafe assumptions in early code.

The Multiboot2 memory map is untrusted input. Firmware-reserved ranges, the kernel image and bootloader information must not be handed out as free frames.

## Decision

Use a fixed-size 4 KiB bitmap allocator for physical frames below 1 GiB during bootstrap. Maintain separate used and reserved bitmaps so that freeing an allocated frame cannot release firmware, kernel or boot-information reservations.

Only type-1 available memory-map entries become candidates. Apply all non-available ranges after available ranges so reserved entries win if the map overlaps. Explicitly reserve the first 1 MiB, the linked kernel image and the Multiboot2 information block.

The allocator returns physical addresses only. It does not establish virtual mappings.

## Alternatives considered

- **Buddy allocator:** deferred until page allocation, coalescing and fragmentation requirements justify the additional metadata and complexity.
- **Dynamic bitmap sized from RAM:** deferred because it requires allocating and mapping the allocator's own metadata before the allocator is available.
- **Manage all reported physical memory:** rejected for this milestone because the current page tables cover only the first 1 GiB.
- **Treat the memory map as trusted:** rejected; every tag, entry size and address range must be validated first.

## Consequences

- Two 1 GiB/4 KiB bitmaps consume 64 KiB in the kernel image.
- The allocator is bounded, deterministic and simple to test, but scans a bitmap and is not intended for high-performance general-purpose allocation.
- The allocator is single-core and has no locking. SMP must not be enabled until allocation synchronisation is designed and tested.
- Expanding beyond 1 GiB requires coordinated page-table and allocator changes.
- Page-table management, virtual mapping, slab allocation, NUMA and ownership tracking remain future work.

## Validation

Host unit tests cover malformed Multiboot2 tags, entry-size/version checks, address overflow, available/reserved overlap, kernel and boot-info reservations, alignment, unique allocation, double-free rejection and attempts to free reserved frames. The QEMU boot test allocates and releases frames using the live bootloader memory map.

## References

- [Multiboot2 specification: memory map tag](https://www.gnu.org/software/grub/manual/multiboot2/multiboot.html)
- [ADR 0010: GRUB Multiboot2 boot protocol](0010-multiboot2-grub-boot-protocol.md)
- [Memory model](../MEMORY_MODEL.md)
