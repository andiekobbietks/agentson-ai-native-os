# ADR 0009: Design for observability, failure handling and recovery

- Status: Accepted as design direction
- Date: 2026-11-27

## Context

A system that boots or runs an inference workload once is not necessarily understandable or operable. Kernel faults, malformed models, resource exhaustion, device failures and agent-tool errors need to be diagnosable. The project also values portability and capability over dependence on a single operational service.

## Decision

- Define deterministic boot diagnostics and explicit error paths before adding complex runtime features.
- Record relevant lifecycle events with stable identifiers and versioned schemas.
- Use AgentSON as an optional event interchange and audit layer, not as a security control or kernel API.
- Keep logs and traces useful without exposing secrets or unrestricted prompt/model contents.
- Define resource limits, timeouts and failure behaviour for agent operations.
- Document recovery, reset and safe-shutdown expectations for each implemented subsystem.
- Avoid making external telemetry or a hosted provider a prerequisite for basic local operation.

## Alternatives considered

- **Treat successful execution as sufficient:** rejected because failures would be difficult to diagnose and reproduce.
- **Make a hosted observability service mandatory:** rejected because it introduces an avoidable runtime dependency.
- **Treat audit events as enforcement:** rejected because recording an action does not prevent it.

## Consequences

- Event schemas, diagnostics and retention require design.
- Observability must be balanced against privacy, storage and performance.
- Recovery behaviour becomes part of acceptance criteria, not an afterthought.

## Validation

- Fault-injection tests cover defined failure paths.
- Logs and traces can be inspected without privileged hosted services.
- Tests verify that secrets and prohibited sensitive payloads are not emitted.
- Recovery steps are exercised and documented before claiming recoverability.
