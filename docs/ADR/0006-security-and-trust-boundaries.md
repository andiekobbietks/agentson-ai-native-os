# ADR 0006: Treat inputs as untrusted and enforce explicit trust boundaries

- Status: Accepted for initial architecture
- Date: 2026-11-27

## Context

The system may process model files, prompts, tool output, device metadata, shared-memory regions and host-provided data. Some of these inputs may be malformed or adversarial. A bare-metal environment also has a different threat model from a conventional application: firmware, hypervisor and physical access may remain outside the project's control.

## Decision

- Document assets, trust boundaries, threats, assumptions and out-of-scope attackers.
- Validate lengths, offsets, alignment, versions and bounds before dereferencing external data.
- Keep model parsing, inference and agent tools outside ring 0 in initial milestones.
- Apply least privilege to filesystem, network, device and process capabilities.
- Deny access by default; require explicit grants and resource limits.
- Treat shared memory as untrusted input even when it is read-only.
- Keep secrets out of source, logs, model artefacts and test fixtures.
- State clearly what the system does not protect against, including malicious firmware or hypervisor unless separately addressed.

## Alternatives considered

- **Trust model and device data because they are locally provisioned:** rejected because local origin does not guarantee integrity.
- **Run all AI functionality in kernel mode:** rejected because it expands privileged attack surface.
- **Claim a secure boundary from documentation alone:** rejected because controls require implementation and adversarial tests.

## Consequences

- Interfaces need explicit validation and failure behaviour.
- Security controls may constrain performance and convenience.
- Threat-model updates are required when new devices, privileges or data flows are introduced.
- Security claims remain limited to implemented and tested controls.

## Validation

- Negative tests cover malformed headers, invalid ranges, oversized inputs and denied capabilities.
- Tests verify that untrusted input cannot bypass access checks.
- Threat-model entries map to implementation controls and tests.
- Security review is required before expanding privileged functionality.
