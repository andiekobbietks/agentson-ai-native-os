# ADR 0014: Controlled PIT timer interrupt using the legacy PIC

- **Status:** Accepted for bootstrap interrupt milestone
- **Date:** 2026-11-27

## Context

The kernel has a tested IDT and exception path but has not yet received an external interrupt. A periodic timer provides a bounded way to validate interrupt entry, stack preservation, EOI handling and return with IRETQ before introducing scheduling.

## Decision

For the first interrupt milestone, remap the legacy 8259 PIC to vectors 0x20–0x2F and program the PIT channel 0 at 100 Hz. Install an IDT gate for IRQ0 at vector 32, unmask only IRQ0, receive at least three ticks, then disable interrupts and mask the PIC again.

The IRQ stub saves general-purpose registers, calls a C dispatcher, acknowledges the master PIC and returns with IRETQ. The test runs in QEMU only.

## Alternatives considered

- **Local APIC timer:** deferred until CPU feature discovery, LAPIC mapping and interrupt-controller abstraction exist.
- **HPET:** deferred; it adds device discovery and MMIO mapping before the basic IRQ contract is validated.
- **Busy-wait timing:** rejected as it does not test interrupt delivery or return semantics.
- **Enable all PIC lines:** rejected; only IRQ0 is unmasked during the test.

## Consequences

- The initial kernel has a verified timer interrupt path in the QEMU environment.
- The PIT is a legacy compatibility device and is not a final production timer source.
- The test temporarily enables maskable interrupts; the kernel masks them again before the deliberate page-fault test.
- No scheduler, preemption, time slicing, APIC, SMP, interrupt prioritisation or device driver framework is implemented.
- The IRQ dispatcher is single-core and not concurrency-safe for SMP.

## Validation

The QEMU test must observe at least three IRQ0 ticks, complete the interrupt handler/IRETQ cycle, mask the PIC and then still pass the controlled page-fault test.

## References

- [Intel 8259A Programmable Interrupt Controller datasheet](https://pdos.csail.mit.edu/6.828/2005/readings/hardware/8259A.pdf)
- [Intel 8254 Programmable Interval Timer datasheet](https://www.intel.com/content/www/us/en/support/articles/000006715/boards-and-kits.html)
- [ADR 0013: IDT and exception diagnostics](0013-idt-and-exception-diagnostics.md)
