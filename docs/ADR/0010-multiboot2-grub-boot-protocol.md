# ADR 0010: GRUB Multiboot2 boot protocol for the first x86-64 milestone

- **Status:** Accepted for the initial prototype
- **Date:** 2026-11-27

## Context

The first independently implemented kernel needs a documented loader contract, a reliable way to pass memory and module metadata, and a QEMU-compatible boot path. The project should avoid depending on an opaque or unavailable boot implementation. The first milestone is a boot proof, not a production boot manager.

## Decision

Use GRUB with the Multiboot2 protocol for the initial x86-64 QEMU prototype. Keep the kernel entry responsible for establishing its own stack, page tables and long-mode transition. Treat all bootloader-provided metadata as untrusted input and validate pointers, alignment and lengths before use.

## Alternatives considered

- **Custom BIOS/UEFI loader:** deferred because it expands the initial scope into firmware interfaces and loader maintenance before the kernel has a tested entry point.
- **Limine or another loader protocol:** viable alternatives, but introducing multiple protocols now would dilute the first boot milestone. Reconsider if later requirements justify it.
- **Copy an upstream boot path:** rejected as the default because this repository is intended to be an independently implemented and independently validated project.

## Consequences

- GRUB, Multiboot2 tooling and ISO creation are build-time dependencies.
- The first entry point starts in 32-bit protected mode and must establish long mode explicitly.
- The first implementation uses a temporary 1 GiB identity map with 2 MiB pages; this is not the final virtual-memory policy.
- The loader's memory map and tags must be parsed with strict bounds checks in the next memory milestone.
- The boot protocol can be replaced later behind a small boot-information adapter if the cost/benefit changes.

## Validation

The first implementation must pass the repository's ELF/Multiboot2 header checks and boot in QEMU, emitting a stable serial success marker and expected debug-exit status. CI must record the result. No physical-hardware or production-readiness claim follows from this decision.

## References

- [Multiboot2 specification](https://www.gnu.org/software/grub/manual/multiboot2/multiboot.html)
- [GRUB manual](https://www.gnu.org/software/grub/manual/grub/grub.html)
