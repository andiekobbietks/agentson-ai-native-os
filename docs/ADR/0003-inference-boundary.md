# ADR 0003: Inference is not a kernel subsystem

- Status: Accepted for initial milestones
- Context: The reference project demonstrates a minimal bare-metal inference path, but model parsing, tokenisation, large allocations and agent tooling increase kernel attack surface.
- Decision: Boot and kernel milestones must work without a model. Initial inference and agent execution run outside ring 0, with narrow, validated interfaces. Bare-metal inference can be a later optional profile after isolation and memory management exist.
- Consequences: The project can validate kernel correctness independently of model availability and can compare its inference runtime with Linux.
