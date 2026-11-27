# Memory milestone 1: Multiboot2 memory map and physical frames

**Implementation status:** Parser, bounded bitmap allocator, host unit tests and QEMU integration added; CI validation pending.

## Implemented

- Bounded Multiboot2 tag traversal with 8-byte alignment and end-tag validation.
- Unique memory-map tag validation, version and entry-size checks, and physical range overflow checks.
- 4 KiB physical-frame bitmap allocator for the first 1 GiB.
- Separate used and reserved bitmaps.
- Reserved-range precedence over available ranges.
- Explicit reservations for low memory, the linked kernel image and the boot-information block.
- Allocation, release, double-free and reserved-frame checks.
- Host-side malformed-input and allocator unit tests.
- QEMU integration that parses the live memory map, allocates two frames, verifies uniqueness/alignment, releases them and emits a success marker.

## Reproduce

```bash
make clean all check
make test-unit
make test
```

The GitHub Actions kernel workflow runs the host unit tests and QEMU boot test as part of `make test`.

## Boundaries

The allocator manages only the first 1 GiB because that is the range covered by the initial identity map. It returns physical addresses but does not map them. It is single-core, has no locking, and is not a production allocator. The page-table manager, IDT, exception handling, interrupt enablement, scheduler, userspace, SMP and device framework remain unimplemented.

## Next

Implement a page-table manager with explicit permissions and map/unmap tests. Then add IDT and exception diagnostics before enabling interrupts or introducing concurrency.
