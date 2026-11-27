# Memory Model

**Status:** Proposed design; implementation pending.

## Address spaces
- Physical addresses identify RAM/device ranges from the boot memory map.
- Kernel virtual addresses are established by explicit page tables.
- User/agent address spaces are a later milestone and must not share unrestricted kernel mappings.
- MMIO and PCI BAR ranges are mapped separately with appropriate cacheability and permissions.

## Huge pages
Mitko Vasilev's demonstration highlights the cost of page-table overhead when mapping very large model files. Evaluate 2 MiB and 1 GiB pages as optional mapping strategies, not universal defaults. Require CPU support, alignment, reserved-memory checks and a fallback to smaller pages. Measure TLB behaviour and boot/runtime costs before choosing.

## Allocator milestones
1. Parse and validate the boot memory map.
2. Reserve kernel image, boot structures, page tables and device regions.
3. Implement a physical-frame allocator with overflow and bounds checks.
4. Add virtual mapping/unmapping with explicit permissions.
5. Add allocation accounting and fragmentation tests.

## Model mapping
Do not put multi-gigabyte weights in the kernel image or boot module by default. Prefer a separately provisioned, read-only model backing region. If using ivshmem, treat its PCI BAR as an untrusted device mapping: validate BAR width, size, alignment, address range and model header before reading. The guest must not assume the host file is trustworthy merely because the mapping is read-only.
