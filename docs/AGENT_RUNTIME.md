# Agent Runtime

**Status:** Proposed; not implemented.

## Placement
The initial agent runtime belongs in an unprivileged process or isolated guest service, not in the kernel. The kernel provides scheduling, memory isolation and narrowly scoped IPC primitives.

## Lifecycle
1. Create an execution identity and session ID.
2. Resolve a policy profile and explicit capability set.
3. Reserve memory, CPU/time and output budgets.
4. Start the agent in an isolated execution context.
5. Validate each tool request against schema, capability and policy.
6. Record request, decision, invocation and result events.
7. Revoke capabilities and release resources on completion or failure.

## Deny by default
No ambient network, filesystem, PCI, DMA, shell or secret access. Tool permissions are explicit, scoped, revocable and time-bounded. User confirmation is required for consequential operations.

## Failure handling
Timeouts, crashes, malformed output and quota exhaustion terminate or suspend the affected execution without taking down the kernel. Recovery must not replay side effects unless the tool contract declares idempotency.
