# Product Requirements

## Purpose

Develop a reproducible research platform exploring operating-system primitives designed for local AI inference and bounded agent execution.

## Users

- OS and systems programmers.
- Local inference and runtime researchers.
- Agent infrastructure developers.
- Contributors interested in auditability and reproducibility.

## MVP requirements

- Boot in QEMU on x86-64.
- Emit deterministic serial boot diagnostics.
- Discover and report available physical memory.
- Provide a testable physical memory allocator.
- Run a small, documented inference workload only after kernel foundations are validated.
- Record agent and inference lifecycle events in an AgentSON-compatible format.

## Quality requirements

- Reproducible build instructions.
- Explicit supported hardware and emulator matrix.
- No unsupported performance or safety claims.
- Clear separation between implemented features, experiments and roadmap items.
