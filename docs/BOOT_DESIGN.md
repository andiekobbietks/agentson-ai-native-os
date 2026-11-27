# Boot Design

**Status:** Proposed; no boot code exists yet.

## First target
x86-64 guest under QEMU, using a Multiboot-compatible loader for the initial prototype. The exact boot protocol and loader version must be pinned in an ADR before implementation.

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

## Acceptance criteria
A first boot milestone requires a reproducible image, QEMU command, captured serial output, exit/timeout handling and a test that checks the expected boot marker. It does not require inference.
