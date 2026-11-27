# ADR 0013: Install IDT gates and diagnose CPU exceptions

- **Status:** Accepted for bootstrap kernel milestones
- **Date:** 2026-11-27

## Context

The kernel needs a defined exception path before it deliberately exercises page faults or begins enabling device interrupts. A missing or malformed IDT can turn a recoverable fault into a triple fault, obscuring the original cause.

## Decision

Install a 256-entry IDT with interrupt gates for CPU exception vectors 0–31. Provide architecture assembly stubs that normalise the stack shape by supplying a zero error code for exceptions that do not push one and preserve the CPU-provided error code for exceptions that do.

The common entry saves general-purpose registers and passes a typed frame to a non-returning C dispatcher. The dispatcher reports the vector, error code and CR2 for page faults. The initial QEMU test deliberately reads an unmapped canonical address and succeeds only if vector 14, CR2 and the expected not-present supervisor-read error code match.

Maskable interrupts remain disabled. No PIC/APIC routing, timer, TSS/IST stack, syscall entry or ring-3 transition is part of this decision.

## Alternatives considered

- **Enable interrupts immediately:** rejected until exception handling and interrupt-controller setup are independently tested.
- **Use a generic untyped stack dump:** rejected because exception error-code differences make offsets ambiguous.
- **Return from all exceptions:** rejected for the bootstrap stage; an unexpected exception is fatal until recovery semantics exist.
- **Use a third-party interrupt framework:** deferred to keep the initial architecture contract inspectable.

## Consequences

- CPU exceptions 0–31 have explicit IDT entries.
- The dispatcher is non-returning and the first test uses QEMU's debug-exit device to signal the expected fault.
- The implementation assumes same-privilege ring-0 exceptions. It does not yet support privilege transitions, IST stacks or safe double-fault recovery.
- Device interrupts remain masked/disabled; this does not establish an operational interrupt subsystem.
- The IDT is diagnostic infrastructure, not a security boundary.

## Validation

The QEMU test must boot through the memory and paging checks, install the IDT, intentionally fault on an unmapped address, print the expected page-fault marker, confirm CR2 and error code, and exit with the expected test status. An unexpected vector or address must fail the test.

## References

- [AMD64 Architecture Programmer's Manual](https://www.amd.com/en/search/documentation/hub.html)
- [Intel 64 and IA-32 Software Developer Manuals](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html)
- [ADR 0012: page-table manager](0012-x86-64-page-table-manager.md)
