# ADR 0017: Host-side deny-by-default capability policy core

- **Status:** Accepted for host policy prototype
- **Date:** 2026-11-27
- **Decision owners:** AgentSON project maintainers

## Context

The agent runtime requires explicit, scoped and revocable permissions. The current kernel does not provide userspace processes, address-space isolation, syscalls or a secure executor. Implementing policy in ring 0 would create a false impression that tool operations are contained.

## Decision

Implement the first policy decision core as a host-side, standard-library Python component. It must deny by default and match grants on exact session, agent, capability and resource strings.

The prototype supports grant expiry/revocation, per-grant call limits, request-bound one-time confirmation, per-session action/output budgets, deadlines, unique request IDs, output reservations and settlement/cancellation. Decisions are recorded in an in-memory audit structure.

The policy core does not execute tools. Any future executor must canonicalise resources independently and enforce the same scope at the point of use, with OS-level isolation and resource controls.

## Alternatives considered

- **Kernel-resident tool execution:** rejected until user-mode processes, memory isolation, syscall boundaries and driver controls exist.
- **Ambient host permissions:** rejected because an agent must not inherit arbitrary filesystem, network, shell, credential or device access.
- **Immediate AgentSON event export:** deferred because the pinned v1.2 schema and ADR-015 describe different serialization shapes. No new event primitive or export format is invented to bridge the discrepancy.

## Consequences and limitations

The policy engine is a testable authorization core, not a sandbox. Exact resource strings are compared; the policy core does not resolve symlinks, canonicalise paths or open resources. It cannot constrain a compromised executor. CPU time, memory, process count and wall-clock enforcement must be implemented by the eventual executor/OS boundary.

Audit records are in-memory only. AgentSON export remains blocked until the canonical v1.2 serialization contract is reconciled and conformance-tested.

## Validation

Tests must cover deny-by-default, exact scope binding, expiry, revocation, call limits, session budgets, output reservation/refund/overrun, deadlines, request replay, one-time human approval, duplicate grant rejection and concurrent authorization under a shared budget.

A passing policy test validates the policy decision core only. It does not validate process isolation or real tool execution.

## Follow-up

Implement an isolated executor with OS-enforced filesystem/network/process boundaries, memory and CPU quotas, cancellation and durable audit. Add AgentSON export only after the schema contract is resolved.
