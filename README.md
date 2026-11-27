# AgentSON AI-Native OS

An independently developed research and engineering project exploring an AI-native, x86-64 bare-metal platform, beginning with a reproducible QEMU target.

**Current maturity:** the independent x86-64 kernel boot, Multiboot2 memory-map parsing, bounded physical-frame allocator, 4 KiB page-table operations, IDT exception diagnostics and a controlled PIT/PIC IRQ0 timer path have been exercised in QEMU through GitHub Actions. The two-task ring-0 preemptive context-switch experiment is QEMU-verified in GitHub Actions run #57. A host-side GGUF inspector and bounded dequantizer for F32, F16, Q4_0, Q4_1, Q5_0, Q5_1, Q8_0 and Q8_1 are implemented, alongside the deny-by-default capability policy core and one read-only workspace-file executor (8 MiB maximum response). Native model inference and an isolated/general-purpose agent runtime are not implemented.

## How the project began

This project deliberately began as a **research scaffold**, not as a claim to have a working operating system. The first stage was to establish a repository in which the problem, prior art, constraints and engineering questions could be investigated before committing to implementation choices.

A bare-metal AI system spans boot, memory management, device boundaries, model formats, inference, agent execution, security and reproducibility. Implementing these concerns without first understanding their dependencies risks avoidable coupling and makes later decisions difficult to inspect or reverse.

The project therefore evolved through these stages:

1. **Initial research scaffold:** establish the repository, purpose and initial questions before introducing kernel code.
2. **Reference investigation:** study public implementations, pin exact revisions and distinguish upstream statements from results reproduced here.
3. **Architecture and threat modelling:** define system boundaries, trust assumptions, interfaces and staged requirements.
4. **Architecture Decision Records:** make consequential choices explicit, including context, alternatives, trade-offs and validation obligations.
5. **Implementation and verification:** proceed through small pull requests, with tests and recorded evidence for each capability.

The first four stages establish the baseline for implementation. They do not imply that the later stages are already complete.

## Engineering approach

This project follows the end-to-end, evidence-led product engineering approach documented in the [Engineering Playbook](https://github.com/andiekobbietks/engineering-playbook) and the engineering philosophy in the [GitHub profile](https://github.com/andiekobbietks). The playbook is a living reference; this repository adopts its relevant practices incrementally and records their actual maturity.

The principles applied here are:

- **Problem framing:** state the problem, intended outcomes, constraints, assumptions and acceptance criteria before implementation.
- **Systems thinking:** design boundaries, interfaces, dependencies and operational consequences as one system.
- **Capability over dependency:** prefer designs that can be understood, operated, tested and changed without unnecessary dependence on a single tool or provider.
- **Evidence over assertion:** trace decisions to primary sources, tests, measurements or explicitly labelled assumptions.
- **Portability over lock-in:** use documented interfaces and replaceable components; verify portability with tests rather than treating it as an aspiration.
- **Security by design:** define trust boundaries, least privilege, input validation and failure behaviour before exposing privileged functionality.
- **Human accountability in AI-augmented development:** AI tools may assist research and implementation, but a human remains responsible for review, risk acceptance and release.
- **Small, reviewable delivery:** use focused branches and pull requests, explicit acceptance criteria, automated checks and documented review.
- **Operational learning:** design for observability, recovery and improvement, not only for a successful demonstration.

These are project engineering rules, not a claim that every future control is already implemented. See [ADR governance](docs/ADR/README.md) and [validation status](docs/VALIDATION.md).

## Research references

The project studies the public work of [Mitko Vasilev](https://github.com/mitkox/qwen38-27b-baremetal-os) and [alesha-pro](https://github.com/alesha-pro/llm.asm) as engineering references. It is an independent project. Their performance and correctness statements remain upstream claims until independently reproduced here.

| Project | Pinned commit | Research relevance |
|---|---|---|
| [alesha-pro/llm.asm](https://github.com/alesha-pro/llm.asm) | [48feccb](https://github.com/alesha-pro/llm.asm/commit/48feccbfd57cb669440f31ff64958d95bb8b848e) | Assembly/kernel implementation and reference build structure |
| [mitkox/qwen38-27b-baremetal-os](https://github.com/mitkox/qwen38-27b-baremetal-os) | [6c43dec](https://github.com/mitkox/qwen38-27b-baremetal-os/commit/6c43decc38aa8ea5fd22dba31360e8004601097d) | Hybrid-model, shared-memory, huge-page and SMP design reference |

Both repositories are reported as MIT-licensed. Before adapting any file, verify its exact licence and copyright notice and record the source path, commit, changes and rationale in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). No upstream implementation source is claimed as copied by the research/documentation baseline.

## Start here

- [Product requirements](docs/PRD.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Architecture Decision Records](docs/ADR/README.md)
- [Threat model](docs/THREAT_MODEL.md)
- [Boot design](docs/BOOT_DESIGN.md)
- [Memory model](docs/MEMORY_MODEL.md)
- [Inference design](docs/INFERENCE_DESIGN.md)
- [Agent runtime](docs/AGENT_RUNTIME.md)
- [Component interfaces](docs/INTERFACES.md)
- [Reference engineering lessons](docs/REFERENCE_ENGINEERING.md)
- [Validation plan](docs/VALIDATION.md)
- [Contributor and AI-agent instructions](AGENTS.md)
- [Windows/WSL2 setup](docs/WINDOWS_WSL2.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

## Inspecting a GGUF model file

The host-side inspector reads GGUF v2/v3 little-endian headers and tensor metadata without loading tensor payloads. The separate tensor decoder can dequantize supported payload buffers:

```bash
python3 tools/gguf_inspect.py path/to/model.gguf
make test-model-format
```

The inspector and decoder are format-validation/reference utilities, not an inference engine. See [inference design](docs/INFERENCE_DESIGN.md) for supported layouts and limitations.

## Roadmap

1. **Research baseline:** reproduce and record the pinned upstream reference build in a separate, isolated checkout.
2. **Boot and kernel foundations:** independent GRUB Multiboot2 x86-64 boot, memory-map parsing, bounded frame allocation, 4 KiB page mapping, IDT exception diagnostics and a controlled legacy timer interrupt path.
3. **Scheduling:** validate the fixed two-task ring-0 context-switch experiment; then design task lifecycle, stack protection and interrupt/locking invariants before broader scheduling.
4. **Concurrency and devices:** SMP correctness, APIC-based interrupt routing and narrowly scoped device support.
5. **Reference inference:** GGUF container inspection and selected tensor dequantization are implemented; tokenizer validation, K-quant formats and a reproducible host-side inference baseline remain before any guest integration.
6. **Agent execution:** isolated runtime, explicit capabilities, resource quotas and denied-operation tests.
7. **Interoperability:** AgentSON, OIDL and JITLLM adapters where their contracts are defined and justified.
8. **Hardening and evaluation:** fault injection, reproducibility, security and performance evaluation.

Each milestone is to be delivered through one or more focused pull requests. A design document or merged ADR is not evidence that the corresponding capability has been implemented.

## Current validation status

| Capability | Status |
|---|---|
| Research, architecture and engineering governance | Present on `main` |
| Reference revisions pinned | Yes; upstream build not yet reproduced |
| Independent x86-64 boot | QEMU-verified |
| Multiboot2 memory-map parser | Unit and QEMU-verified |
| Bounded physical-frame allocator | Unit and QEMU-verified; limited to first 1 GiB |
| 4 KiB page-table map/unmap/translate | QEMU-verified; single-core bootstrap only |
| IDT and expected page-fault diagnostics | QEMU-verified |
| PIT/PIC IRQ0 timer path | QEMU-verified; legacy PIC, single-core test path |
| Two-task ring-0 context switching | QEMU-verified in GitHub Actions run #46; both tasks ran, boot context resumed and page-fault test passed |
| SMP, userspace and process isolation | Not implemented |
| GGUF metadata/tensor-directory inspection | Host-side bounded parser and malformed-file tests; no model execution |\n| GGUF tensor dequantization | Host-side reference decoder for eight tensor types; no matrix multiplication or inference |
| Native model loading/inference | Not implemented |
| Agent capability policy | Host-side exact-scope grants, revocation, approvals and session budgets |
| Read-only workspace executor | One file-read tool with exact grants, no-follow opens and output limits; no process isolation |
| Agent runtime / sandbox | Not implemented |
| AgentSON trace integration/replay | Design only |
| CI | Documentation hygiene, freestanding kernel build, host memory tests and QEMU smoke test |

## Scope and safety

This is experimental operating-system research, not a production operating system or a hardened boundary against a malicious hypervisor, firmware or physical attacker. Current task execution is privileged ring 0 and must not be used for untrusted code. Use disposable virtual machines. Do not pass through host disks or expose unrestricted devices. Do not claim performance, security or correctness without reproducible evidence.

## Licence

Original project documentation and independently authored material are licensed under Apache-2.0 unless a file states otherwise. Third-party components retain their own licences and notices. Model weights and datasets may have separate terms.
