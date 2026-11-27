# Exception milestone 1: IDT and page-fault diagnostics

**Implementation status:** Passed in GitHub Actions run #27: IDT installed and the expected supervisor page fault was diagnosed with the correct CR2 and error code.

## Implemented

- Shared COM1 serial driver.
- 256-entry IDT with interrupt gates for CPU exception vectors 0–31.
- Assembly stubs that normalise error-code and no-error-code stack layouts.
- General-purpose register save frame and C exception dispatcher.
- Page-fault diagnostics including error code and CR2.
- QEMU test that reads an unmapped canonical address and expects a controlled page-fault exit.

## Reproduce

```bash
make clean all check
make test
```

## Deliberate limitations

This is exception diagnostics, not a complete interrupt subsystem. Maskable interrupts remain disabled. There is no PIC/APIC routing, timer, scheduler, TSS, IST stack, double-fault recovery, syscall gate, privilege transition or ring-3 support. Do not run untrusted code in this kernel.

## Next

Add a minimal GDT/TSS policy with a dedicated double-fault IST stack, then introduce a controlled timer interrupt and verify interrupt masking/acknowledgement before considering SMP.
