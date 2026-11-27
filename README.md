# AgentSON AI-Native OS

An independently developed, research-first AI-native bare-metal platform. The initial implementation target is x86-64 in QEMU, using publicly inspectable source and reproducible validation.

**Status:** Project scaffold. No kernel implementation has been imported or validated yet.

## Goals

- Establish a reproducible bare-metal boot and test baseline.
- Build kernel capabilities incrementally, starting with boot, serial output and memory discovery.
- Integrate local inference only after the kernel baseline is stable.
- Keep agent execution bounded, inspectable and permissioned.
- Emit portable AgentSON-compatible execution records.

## Source strategy

The initial research reference is [`alesha-pro/llm.asm`](https://github.com/alesha-pro/llm.asm), particularly its `02-baremetal-os/` implementation and Makefile. This project is intended to be an independent implementation and integration workspace, not a blind copy. Review upstream source, commit history, dependencies and licence before importing or adapting any code. Preserve required notices for any reused MIT-licensed portions.

The restricted-source `tomstuhl/agentos` project is an architectural reference only. This project must not depend on unavailable source.

## Current validation status

| Capability | Status |
|---|---|
| Repository scaffold | Created |
| Upstream source and licence identified | Initial inspection only |
| Reproducible upstream build | Not yet run |
| Independent kernel boot | Not implemented |
| Bare-metal inference | Not implemented |
| AgentSON event integration | Design placeholder |
| Security review | Not started |

## Roadmap

1. **P0 - Baseline audit:** record upstream commit SHA, source inventory, licence, toolchain and build instructions; reproduce upstream build in a disposable environment.
2. **P1 - Boot baseline:** create a minimal x86-64 boot target with serial diagnostics and QEMU smoke test.
3. **P2 - Kernel foundations:** memory map, physical allocator, exceptions and interrupt handling.
4. **P3 - SMP and devices:** CPU discovery, AP startup and carefully scoped device support.
5. **P4 - Inference:** model format, tokenizer, memory requirements and inference backend.
6. **P5 - Agent runtime:** bounded tool execution, capability checks and explicit permission boundaries.
7. **P6 - AgentSON:** versioned event schema, provenance, integrity and replay tests.
8. **P7 - Reliability:** fault injection, repeatability, performance methodology and security review.

## Repository layout

- `docs/` - product requirements, architecture, research, roadmap and validation.
- `kernel/` - future boot and kernel implementation.
- `inference/` - future model and inference components.
- `agents/` - future agent runtime and permission model.
- `hardware/` - architecture-specific code and capability descriptors.
- `integrations/` - AgentSON, OIDL and inference-runtime adapters.
- `tests/` - smoke, unit, integration and determinism tests.
- `scripts/` - reproducibility and development helpers.

## Non-goals for the first milestone

- Replacing a daily-driver operating system.
- Running untrusted autonomous agents with unrestricted hardware access.
- Claiming production readiness or real-time safety.
- Claiming benchmark results before independent reproduction.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Every capability claim should link to a reproducible test, benchmark procedure or clearly labelled external source.
