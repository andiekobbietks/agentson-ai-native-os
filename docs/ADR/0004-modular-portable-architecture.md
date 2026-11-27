# ADR 0004: Prefer modular boundaries and replaceable components

- Status: Accepted for initial architecture
- Date: 2026-11-27

## Context

The platform spans hardware-specific boot code, kernel primitives, device access, inference, model storage and agent tooling. A monolithic design would make it harder to test components independently, change execution environments or compare a bare-metal path with a host reference.

Portability is a stated engineering principle, but portability cannot be inferred from using open formats or interfaces alone. It must be demonstrated through substitution and compatibility tests.

## Decision

- Separate architecture-specific code from portable interfaces and shared logic.
- Keep boot, kernel, model lifecycle, inference and agent-runtime responsibilities in explicit layers.
- Define narrow, versioned interfaces at component boundaries.
- Keep the model payload independent from the boot image.
- Preserve a host/Linux reference path where it improves correctness testing.
- Avoid a mandatory dependency on a single model provider, orchestration tool or cloud service.
- Record unavoidable platform-specific assumptions and test replacement paths where practical.

## Alternatives considered

- **Monolithic kernel and inference implementation:** rejected for the initial milestones because it increases privileged code and couples unrelated lifecycles.
- **Premature plugin framework:** rejected because abstraction without a demonstrated second implementation adds complexity without proving replaceability.
- **Claim portability from standards compliance alone:** rejected because compatible formats do not prove operational substitution.

## Consequences

- Interfaces and versioning require explicit design and maintenance.
- Some boundaries may add overhead; performance must be measured before collapsing them.
- The architecture can support host-side tests and future alternative backends.
- Portability claims require a documented substitution test.

## Validation

- Unit and integration tests exercise component contracts.
- At least one replaceability test is required before making a portability claim for a component.
- Build and runtime dependencies are inventoried and reviewed.
- Interface changes are versioned and recorded.
