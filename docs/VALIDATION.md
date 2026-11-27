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
| QEMU boot smoke test | Serial output and exit status | Not implemented |
| Memory map | Parsed ranges and bounds checks | Not implemented |
| Allocator | Unit tests and boundary tests | Not implemented |
| Inference correctness | Fixed prompts and token output | Not implemented |
| Agent permissions | Positive and negative capability tests | Not implemented |
| AgentSON trace | Schema validation and replay | Not implemented |
