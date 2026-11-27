# Validation Plan

## Evidence rules

- Distinguish source claims from locally reproduced results.
- Record exact commit SHA, host OS, CPU, RAM, toolchain versions and command lines.
- Save build logs and hashes of generated artifacts.
- Benchmark only after correctness tests pass.
- Do not compare results unless model, quantisation, context, prompt, hardware and measurement method are comparable.

## Initial matrix

| Test | Expected evidence | Status |
|---|---|---|
| Upstream baseline build | Clean build log and artifact hash | Not run |
| QEMU boot smoke test | Serial output and expected debug-exit status | Passed in GitHub Actions run #11 |
| Multiboot2 memory map | Validated tags, entry bounds and memory regions | Implemented; unit/QEMU validation in this PR |
| Memory map | Parsed ranges and bounds checks | Not implemented |
| Physical-frame allocator | Reserved-range handling, alignment, allocation/free tests | Passed in GitHub Actions run #13 |
| Page-table manager | Create tables, split huge page, map/write/translate/unmap | Passed in GitHub Actions run #22 |
| IDT and exception path | Install vectors 0–31; handle expected supervisor page fault | Passed in GitHub Actions run #27 |
| Inference correctness | Fixed prompts and token output | Not implemented |
| Agent permissions | Positive and negative capability tests | Not implemented |
| AgentSON trace | Schema validation and replay | Not implemented |
