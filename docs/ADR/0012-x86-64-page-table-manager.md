# ADR 0012: Explicit 4 KiB page-table manager

- **Status:** Accepted for bootstrap kernel milestones
- **Date:** 2026-11-27

## Context

The kernel needs to map physical frames into virtual addresses before it can isolate future subsystems or userspace. The boot stub currently establishes a 1 GiB identity map using 2 MiB PDEs. A page-table manager must coexist with that bootstrap mapping and safely create 4 KiB mappings.

## Decision

Implement a small x86-64 page-table manager that:

- Walks the active PML4/PDPT/PD/PT hierarchy.
- Creates missing intermediate tables from the physical-frame allocator.
- Maps, unmaps and translates 4 KiB pages.
- Splits an existing 2 MiB PDE into 512 4 KiB PTEs when a sub-page needs to be unmapped.
- Invalidates the affected TLB entry after mapping changes.
- Accepts only aligned physical frames below the currently identity-mapped 1 GiB boundary.
- Supports present, writable and user flags; NX and cacheability controls are deferred until their CPU feature and device-mapping policies are specified.

## Alternatives considered

- **Replace the boot map immediately:** rejected because it would add a second large change before the initial mapping can be manipulated and tested.
- **Only support new empty virtual ranges:** insufficient because the bootstrap 2 MiB identity map occupies the first GiB and must be safely split.
- **Use 2 MiB pages everywhere:** rejected because later page-level permissions, guard pages and small mappings require 4 KiB granularity.
- **Adopt a third-party paging library:** rejected for the bootstrap core to keep architecture state and invariants explicit.

## Consequences

- Page-table pages are allocated from the bounded frame allocator and are identity-accessible while below 1 GiB.
- Empty page-table pages are not reclaimed yet.
- The manager is single-core and has no locking or shootdown protocol; do not enable SMP.
- It does not yet implement NX, PAT/cacheability policy, guard regions, page ownership, copy-on-write, demand paging or user/kernel isolation policy.
- Physical frames are not automatically freed when a mapping is removed; ownership remains with the caller.

## Validation

The QEMU test must create a new PDPT branch at 1 GiB, split an existing 2 MiB identity mapping, map frames, write/read through both virtual aliases, verify translation, reject duplicate/unaligned mappings, unmap and then release the data frames.

## References

- [AMD64 Architecture Programmer's Manual, Volume 2](https://www.amd.com/en/search/documentation/hub.html)
- [Memory model](../MEMORY_MODEL.md)
- [ADR 0011: bitmap frame allocator](0011-bitmap-frame-allocator.md)
