# Architecture Decision Records

This directory records consequential technical and product-engineering decisions for AgentSON AI-Native OS.

ADRs are decision records, not implementation tickets. An accepted decision describes the chosen direction and the evidence or validation still required. The validation matrix and implementation code determine whether a capability is actually delivered.

## Decision register

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-research-first-scope.md) | Research-first scope and staged implementation | Accepted |
| [0002](0002-model-memory-boundary.md) | Keep model weights outside the kernel image | Accepted for research baseline |
| [0003](0003-inference-boundary.md) | Keep initial inference outside the privileged kernel | Accepted for initial milestones |
| [0004](0004-modular-portable-architecture.md) | Modular boundaries and replaceable components | Accepted for initial architecture |
| [0005](0005-evidence-and-reproducibility.md) | Evidence, reproducibility and benchmark integrity | Accepted |
| [0006](0006-security-and-trust-boundaries.md) | Security boundaries and least privilege | Accepted for initial architecture |
| [0007](0007-ai-assisted-engineering.md) | Human-accountable AI-augmented engineering | Accepted |
| [0008](0008-review-and-release-governance.md) | Small changes, review and controlled release | Accepted |
| [0009](0009-observability-and-recovery.md) | Observability, failure handling and recovery | Accepted as design direction |
| [0010](0010-multiboot2-grub-boot-protocol.md) | GRUB Multiboot2 boot protocol for the first x86-64 milestone | Accepted for initial prototype |
| [0011](0011-bitmap-frame-allocator.md) | Bounded 4 KiB bitmap frame allocator for the initial 1 GiB map | Accepted for initial kernel milestones |
| [0012](0012-x86-64-page-table-manager.md) | Explicit 4 KiB page mapping, unmapping and translation | Accepted for bootstrap kernel milestones |
| [0013](0013-idt-and-exception-diagnostics.md) | Install IDT gates and diagnose CPU exceptions before enabling interrupts | Accepted for bootstrap kernel milestones |
| [0014](0014-pit-timer-interrupt.md) | Use PIT and remapped legacy PIC for a controlled IRQ0 timer test | Accepted for bootstrap interrupt milestone |
| [0015](0015-preemptive-kernel-task-scheduler.md) | Two-task ring-0 round-robin scheduling from timer interrupt frames | Accepted for two-task QEMU prototype |
| [0016](0016-gguf-model-container.md) | Use GGUF for initial host-side model-container inspection | Accepted for inspection prototype |
| [0017](0017-agent-capability-policy-core.md) | Host-side deny-by-default capability policy core | Accepted for host policy prototype |
| [0018](0018-workspace-read-executor.md) | Read-only workspace executor with descriptor-relative no-follow opens | Accepted for initial host-side tool prototype |
| [0019](0019-gguf-tensor-dequantization.md) | Host-side GGUF tensor dequantization for selected scalar and block types | Accepted for reference decoder prototype |

## When to write an ADR

Write an ADR when a decision materially affects system structure, security, interfaces, portability, dependencies, data handling, operational behaviour or future change cost. Do not create an ADR for every code edit.

## Lifecycle

- **Proposed:** under discussion; not an approved project constraint.
- **Accepted:** selected for the stated scope; implementation and validation may still be outstanding.
- **Superseded:** replaced by a later ADR, which must link back to it.
- **Deprecated:** no longer recommended, with rationale recorded.

An ADR is not silently rewritten after acceptance. If context changes, add a new ADR and mark the earlier one superseded. Correct factual errors transparently and retain the decision history.

## Required structure

1. Title and unique number.
2. Status and date.
3. Context: problem, constraints, assumptions and evidence.
4. Decision: what is being chosen and the scope of the choice.
5. Alternatives considered, including reasons for rejection.
6. Consequences: benefits, costs, risks and follow-on work.
7. Validation: how the decision will be tested and what evidence is required.
8. References: primary sources, exact revisions and relevant project artefacts.

ADRs should be concise enough to review and specific enough to guide implementation. Link related requirements, threat-model entries, issues, pull requests and tests where available.

## Governance

ADRs follow the repository's normal pull-request process. AI-assisted drafting is permitted, but the author and reviewer remain accountable for source accuracy, trade-offs and the final decision. Do not mark a decision accepted merely because an AI tool suggested it or because a PR merged.
