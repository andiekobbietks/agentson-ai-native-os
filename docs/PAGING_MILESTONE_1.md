# Paging milestone 1: 4 KiB page-table management

**Implementation status:** Passed in GitHub Actions run #19, including page-table creation, huge-page splitting, alias writes, translation and unmapping.

## Implemented

- Exported bootstrap PML4 root.
- PML4/PDPT/PD/PT traversal and allocation of missing intermediate tables.
- 4 KiB map, unmap and translation operations.
- 2 MiB huge-page splitting when a 4 KiB sub-page must be unmapped.
- TLB invalidation for changed virtual pages.
- Canonical virtual-address, physical-address range, alignment and flag checks.
- QEMU tests for a new 1 GiB PDPT branch, huge-page split, writes through aliases, translation, duplicate/unaligned mapping rejection and unmapping.

## Reproduce

```bash
make clean all check
make test
```

## Deliberate limitations

The manager supports only physical frames below 1 GiB, uses the initial identity map to access page-table pages, and is single-core. It has no TLB shootdown, SMP locks, page-table reclamation, NX, cacheability policy, guard pages, demand paging, copy-on-write or user/kernel isolation policy. It does not make the kernel safe for untrusted userspace.

## Next

Install an IDT and exception stubs, report register state and page-fault error codes over serial, and test deliberate fault cases before enabling maskable interrupts.
