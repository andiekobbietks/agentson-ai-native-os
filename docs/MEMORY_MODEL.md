# Memory Model

**Status:** The Multiboot2 parser, bounded physical-frame allocator, 4 KiB page-table operations, IDT exception diagnostics, PIT/PIC IRQ0 path and fixed two-task ring-0 scheduler have passed their documented host/QEMU checks. The scheduler prototype passed GitHub Actions run #48.

## Address spaces

- Physical addresses identify RAM/device ranges from the boot memory map.
- The initial kernel identity maps physical addresses from 0 through 1 GiB using 2 MiB pages.
- The current allocator manages only 4 KiB frames below 1 GiB. It does not itself map allocated frames into a new virtual address space.
- The page-table manager supports 4 KiB map/unmap/translate operations and splitting a 2 MiB huge-page mapping. The bootstrap identity map remains limited to the first 1 GiB.
- User/agent address spaces are a later milestone and must not share unrestricted kernel mappings.
- MMIO and PCI BAR ranges are mapped separately with appropriate cacheability and permissions.

## Multiboot2 memory map

The parser validates the information block size, reserved header field, tag bounds and alignment, the unique memory-map tag, entry size/version, end tag and address-range overflow. It retains a bounded view of the entries rather than copying an unbounded bootloader structure.

The parser treats bootloader data as untrusted. Unknown tags are skipped only after their declared sizes and aligned extents have been checked.

## Physical-frame allocator

The initial allocator uses two static bitmaps for the first 1 GiB:

- A used bitmap records allocated or unavailable frames.
- A reserved bitmap prevents freeing firmware/kernel/boot-reserved frames.
- Frames are 4 KiB aligned.
- Only firmware type-1 available regions become candidates.
- Firmware-reserved and other non-available ranges take precedence over overlapping available entries.
- The first 1 MiB, kernel image and Multiboot2 information block are reserved explicitly.
- The allocator returns physical addresses; it does not create page-table mappings.

The 1 GiB limit is deliberate: it matches the temporary identity map. Raising the limit requires changing page-table coverage and allocator metadata together, with overflow and boundary tests.

## Deliberate limitations

The allocator is a single-core bootstrap allocator. It has no SMP locking, NUMA awareness, buddy coalescing, slab allocation, page ownership metadata or virtual mapping integration. Do not call it concurrently. It is not a general-purpose production allocator. The scheduler prototype is also single-core, fixed at two ring-0 tasks, and has no guarded stacks, userspace isolation or general task lifecycle.

## Huge pages

Mitko Vasilev's demonstration highlights the cost of page-table overhead when mapping very large model files. Evaluate 2 MiB and 1 GiB pages as optional mapping strategies, not universal defaults. Require CPU support, alignment, reserved-memory checks and a fallback to smaller pages. Measure TLB behaviour and boot/runtime costs before choosing.

## Model mapping

Do not put multi-gigabyte weights in the kernel image or boot module by default. Prefer a separately provisioned, read-only model backing region. If using ivshmem, treat its PCI BAR as an untrusted device mapping: validate BAR width, size, alignment, address range and model header before reading. The guest must not assume the host file is trustworthy merely because the mapping is read-only.
