# Boot Design

**Status:** Initial implementation merged and verified by GitHub Actions run #11. Memory-map and allocator follow-on is verified by run #13.

## First target
x86-64 guest under QEMU, using GRUB with the Multiboot2 protocol for the initial prototype. The protocol choice is recorded in ADR 0010; the GRUB package version is supplied by the build environment and must be captured in successful CI evidence.

## Boot phases
1. Firmware/virtual machine initialises the platform.
2. Bootloader loads the kernel image and supplies a documented boot-information structure.
3. 32-bit entry validates the boot magic and information pointer.
4. Early assembly establishes a known stack and minimal page tables.
5. CPU feature checks verify required long-mode and SIMD features before use.
6. Transition to long mode and enter the 64-bit kernel.
7. Initialise serial diagnostics before complex subsystems.
8. Validate and record the memory map; reserve kernel, boot data and module ranges.
9. Initialise exception handlers and a minimal allocator.
10. Emit a machine-readable boot-complete marker and halt or enter the test loop.

## Initial constraints
- No model loading during early boot.
- No network or writable host-disk passthrough.
- Do not assume physical addresses are identity mapped unless the page tables explicitly establish it.
- Validate all bootloader-provided pointers and lengths.
- Keep a serial-only diagnostic path independent of VGA.

## Current implementation boundary

The initial entry stub establishes a 16 KiB stack, maps the first 1 GiB with 2 MiB pages, enables PAE and long mode, and transfers control to a freestanding x86-64 C kernel. The kernel initialises COM1, validates the Multiboot2 magic and bounded information structure, parses the memory map, initialises the physical-frame allocator, emits a success marker and exits through QEMU's test-only debug-exit device. See [boot milestone 1](BOOT_MILESTONE_1.md) and [memory milestone 1](MEMORY_MILESTONE_1.md).

The implementation does not yet parse the memory map, install an IDT, enable interrupts, or provide an allocator. The current identity map is deliberately temporary and is not a production memory-protection policy.

## Acceptance criteria
A first boot milestone requires a reproducible image, QEMU command, captured serial output, exit/timeout handling and a test that checks the expected boot marker. It does not require inference.
