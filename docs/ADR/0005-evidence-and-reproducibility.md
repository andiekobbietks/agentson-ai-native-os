# ADR 0005: Make evidence and reproducibility part of delivery

- Status: Accepted
- Date: 2026-11-27

## Context

Bare-metal and inference performance claims are sensitive to hardware, toolchain, model revision, quantisation, workload and measurement method. Upstream demonstrations are useful research inputs but do not establish that this repository has reproduced their results.

## Decision

For each meaningful build, test or benchmark, record as applicable:

- Repository commit and dirty/clean working-tree state.
- Host OS, CPU, RAM, firmware or emulator version.
- Compiler, assembler, linker and build-tool versions.
- Exact commands, configuration and relevant environment variables.
- Input/model revision, format and quantisation.
- Exit status, logs and generated-artifact hashes.
- Test workload, measurement method, repetitions and limitations.

Correctness checks precede performance comparisons. Numerical results must be compared against an independent reference where feasible. Determinism claims must state the tested CPU/thread configurations and tolerances.

## Alternatives considered

- **Narrative-only test reports:** rejected because they cannot reliably reproduce the environment or command sequence.
- **Benchmark numbers without workload context:** rejected because the figures are not meaningfully comparable.
- **Treat upstream evidence as local evidence:** rejected because it misrepresents what this project has validated.

## Consequences

- Evidence capture adds work to each milestone.
- Benchmark reports may be less impressive but more useful and defensible.
- CI should automate repeatable checks, while hardware-dependent tests must clearly report their environment and limits.

## Validation

- Validation entries link to logs or artefacts where available.
- Benchmark reports include hardware, software, workload and methodology.
- A result is not marked passed when it was skipped, inferred or only observed upstream.
