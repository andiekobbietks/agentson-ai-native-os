# ADR 0001: Establish a research-first scope before implementation

- Status: Accepted
- Date: 2026-11-27

## Context

A bare-metal AI platform crosses several complex domains: firmware and boot, CPU architecture, memory management, devices, model formats, inference, agent execution and security. Beginning with a broad implementation before understanding these dependencies risks copying assumptions from a reference project, coupling unrelated components and making unsupported claims.

The project therefore began as a research scaffold. Its purpose was to create a traceable place to frame the problem, inspect prior art, record constraints, define boundaries and plan measurable implementation milestones.

## Decision

Adopt a research-first, evidence-led sequence:

1. Frame the problem, target users, intended outcomes and constraints.
2. Investigate primary sources and pin the exact revisions used.
3. Define architecture, trust boundaries, interfaces and acceptance criteria.
4. Record consequential decisions as ADRs.
5. Implement in small, independently testable milestones.
6. Verify each capability and update the validation record before describing it as implemented.

This decision governs project sequencing. It does not prohibit prototypes or experiments; experiments must be labelled and must not be confused with supported product capabilities.

## Alternatives considered

- **Immediate full-system implementation:** rejected because it would combine too many unvalidated concerns and make failures difficult to isolate.
- **Wholesale adaptation of a reference repository:** rejected because it would obscure provenance, licensing, architectural ownership and independent validation.
- **Documentation without implementation gates:** rejected because design intent can be mistaken for delivered functionality.

## Consequences

- Early repository history and research artefacts remain visible as part of the engineering provenance.
- Architecture and implementation can evolve through reviewable changes.
- Initial delivery takes longer than a single unstructured prototype, but creates clearer evidence and lower decision ambiguity.
- The roadmap must distinguish research, design, prototype and validated implementation.

## Validation

- Every milestone has explicit acceptance criteria.
- Each implementation PR links to relevant ADRs and validation evidence.
- README and status tables describe only capabilities demonstrated in this repository.
- Upstream results are attributed to their source until independently reproduced.
