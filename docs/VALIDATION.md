# Validation Plan

## Evidence rules

- Distinguish source claims from locally reproduced results.
- Record exact commit SHA, host OS, CPU, RAM, toolchain versions and command lines.
- Save build logs and hashes of generated artifacts.
- Benchmark only after correctness tests pass.
- Do not compare results unless model, quantisation, context, prompt, hardware and measurement method are comparable.
- A merged PR is not itself validation evidence; retain the relevant CI run, serial markers, exit status and test artifacts.

## Current milestone matrix

| Test | Expected evidence | Status |
|---|---|---|
| Upstream baseline build | Clean build log, pinned revision and artifact hash | Not run in this project |
| Independent x86-64 boot | ELF/ISO build, long-mode marker, Multiboot2 validation and expected QEMU exit | Passed in GitHub Actions |
| Multiboot2 memory map | Tag bounds, version/entry size, alignment and malformed-input tests | Unit and QEMU tests passed |
| Physical-frame allocator | Reserved-range handling, alignment, allocation/free and duplicate-free rejection | Unit and QEMU tests passed |
| Page-table manager | Intermediate table allocation, huge-page split, map/write/translate/unmap | Passed in GitHub Actions run #22 |
| IDT and exception path | Install vectors 0–31; expected supervisor not-present page fault, CR2 and error code | Passed in GitHub Actions run #29 |
| PIT timer IRQ | PIC remap, vector 32, PIT ticks, EOI, IRETQ and timer mask | Passed in GitHub Actions; main commit records run #36 |
| Two-task context switch | Both task counters advance, boot context resumes, timer stops, expected page fault still passes | Passed in GitHub Actions run #48 (QEMU) |
| SMP | AP startup, per-core state, locking and TLB shootdown tests | Not implemented |
| Model loading/inference | Validated model/tokenizer fixtures, deterministic fixed-prompt output and reference comparison | Not implemented |
| GGUF model inspection | Header/version, metadata, arrays, tensor directory, alignment, bounds and malformed-file tests | Passed in model-format workflow #5 (17 tests) |\n| Agent policy core | Exact grants, expiry/revocation, request-bound approvals, budgets, replay protection and concurrent calls | Passed in agent-policy workflow #1 (19 tests) |\n| Isolated agent execution | Process/VM isolation, syscall policy and OS-enforced quotas | Not implemented |
| AgentSON trace | Schema validation, ordering, integrity, replay and failure tests | Not implemented |

## Reproduction

On Ubuntu or WSL2 Ubuntu, install the packages listed in [Windows/WSL2 setup](WINDOWS_WSL2.md), then run:

```bash
make toolchain-check
make clean all check
make test
```

The QEMU test runs in a disposable virtual machine and checks serial markers plus the expected debug-exit status. GitHub Actions runs the same target. Do not use physical hardware or pass host disks/devices through to the guest.

## Evidence still required

The current bootstrap kernel does not establish production correctness, isolation or security. Before expanding the implementation, add targeted negative tests, stack and interrupt invariants, fault injection, reproducible artifact hashes and review of the actual workflow output. The two-task scheduler experiment passed GitHub Actions run #46, including its QEMU serial-marker and expected-exit checks. Broader scheduler correctness, stack guards, interrupt nesting and SMP remain unvalidated.
