# Boot milestone 1: x86-64 serial boot

**Implementation status:** Passed in GitHub Actions run #11. The follow-on memory-map and physical-frame allocator is documented in [memory milestone 1](MEMORY_MILESTONE_1.md) and verified in run #13.

## Implemented in this milestone

- GRUB Multiboot2 header and 32-bit protected-mode entry.
- Early stack and page-table hierarchy.
- Identity mapping of the first 1 GiB using 2 MiB pages.
- PAE and EFER.LME setup, paging enablement and transition to 64-bit long mode.
- Minimal freestanding x86-64 C kernel and COM1 serial diagnostics.
- Validation of the Multiboot2 magic, information pointer, alignment and total-size bounds.
- QEMU debug-exit success path, ISO build and serial-marker smoke test.

## Reproduce

On Ubuntu or WSL2 Ubuntu, install the packages listed in docs/WINDOWS_WSL2.md, then run:

```bash
make toolchain-check
make clean all check
make test
```

The test boots a disposable QEMU guest with 512 MiB RAM and checks for the long-mode, Multiboot2 validation and BOOT_OK serial markers. It also checks the expected QEMU debug-exit status. The workflow in .github/workflows/kernel-boot.yml runs the same build and smoke test on GitHub Actions.

## Deliberate limitations

This is a boot proof, not yet a general-purpose kernel. The current page tables map only the first 1 GiB with writable 2 MiB pages. This boot milestone did not include a memory-map parser or allocator; those were added in the follow-on memory milestone. There is still no page-table manager, IDT, exception recovery, scheduler, userspace, SMP, device framework, model loader, inference engine or agent runtime. Interrupts remain disabled. The kernel exits after reporting a successful boot.

Do not use this kernel on physical hardware. Do not pass host disks or sensitive host devices into QEMU. The QEMU debug-exit device is a test harness mechanism, not a production kernel interface.

## Next milestone

Parse the Multiboot2 memory map with strict bounds checks, reserve kernel and boot allocations, and implement a tested physical-frame allocator before broadening the memory map or enabling interrupts.
