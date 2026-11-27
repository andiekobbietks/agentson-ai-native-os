# Timer milestone 1: controlled PIT/PIC interrupt

**Implementation status:** Passed in GitHub Actions run #34: three PIT IRQ0 ticks were received, acknowledged and returned through IRETQ before the expected page fault.

## Implemented

- Legacy PIC remapped to vectors 0x20–0x2F.
- Only master IRQ0 unmasked during the test.
- PIT channel 0 programmed at 100 Hz.
- IDT vector 32 connected to the IRQ0 assembly stub.
- General-purpose register save/restore and IRETQ return path.
- C dispatcher increments a tick counter and acknowledges the master PIC.
- Kernel waits for three ticks, disables interrupts and masks the PIC before the page-fault test.

## Reproduce

```bash
make clean all check
make test
```

## Deliberate limitations

This validates one legacy timer interrupt path, not a production interrupt controller. There is no APIC/HPET, scheduler, preemption, time slicing, interrupt priority policy, SMP or device driver framework. The timer test is single-core and QEMU-specific.

## Next

Introduce a minimal cooperative task scheduler with explicit stacks and task states. Only consider preemptive switching after interrupt-frame ownership, FPU/SIMD state and per-CPU state have a documented and tested design.
