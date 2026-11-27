# Agent Runtime

**Status:** Host-side deny-by-default capability policy core and one read-only workspace-file executor implemented; general tool execution, process isolation and a complete agent runtime are not implemented.

## Placement

The policy core belongs in an unprivileged host process. The kernel currently provides a single-core ring-0 task-switching prototype, not user processes, syscalls, address-space isolation or a sandbox. Do not move policy decisions or tool execution into ring 0.

## Implemented policy core

The host-side policy engine currently provides:

- exact session, agent, capability and resource matching;
- deny-by-default behaviour when no matching grant exists;
- grant expiry, immediate revocation and per-grant call limits;
- request-bound, expiring, one-time human approval for grants that require confirmation;
- per-session action limits, output-byte reservations and a session deadline;
- single-use request identifiers to reject replayed authorization requests;
- settlement/cancellation of output reservations, and session lockout after an executor output-limit violation;
- thread-safe authorization and in-memory decision audit records.

Resource scopes are exact strings. Wildcards are rejected. Grant expiry and the session deadline are checked when a request is authorised; they do not terminate an operation already in progress. Output reservations are accounting controls, not a substitute for an executor-side output limiter. The policy engine itself does not access resources. The workspace executor validates relative path components and uses descriptor-relative no-follow opens; future executors must independently enforce their own resource boundaries at the point of use.

## Execution contract

1. The host runtime creates a session and an explicit resource budget.
2. A trusted policy authority issues grants scoped to one session, agent, capability and exact resource.
3. The agent proposes a typed request with a unique request ID and output reservation.
4. The policy core returns allow/deny and records the decision.
5. Only an executor may perform an allowed operation, and it must enforce OS-level isolation and output limits.
6. The executor settles or cancels the reservation and reports the result.
7. Grants are revoked and session resources released on completion or failure.

An allow decision is permission to attempt an operation, not proof that the operation is safe or that the executor enforced the boundary.

## Read-only workspace executor

The initial executor exposes only `workspace.read` for one regular file beneath a trusted absolute workspace root. It constructs an exact `workspace:/relative/path` resource, obtains a policy decision, and uses descriptor-relative `O_NOFOLLOW` / `O_DIRECTORY` opens for each path component. It rejects traversal, symlinks, non-regular files and device changes, checks file metadata before and after reading, and enforces the reserved output limit.

The root path and session/agent identities are trusted host configuration. This tool is Linux/POSIX-specific. It does not write files, list directories, execute commands, connect to networks or create processes. It does not prevent hard links within the workspace from referring to data also reachable elsewhere, and it does not provide process isolation. The workspace must be curated by the host.

## AgentSON compatibility gate

AgentSON integration is deliberately not emitted yet. At the pinned AgentSON repository revision [3ced731](https://github.com/andiekobbietks/AgentSON/commit/3ced7316c64802e289c050de8903838ee160df87):

- the committed v1.2 JSON Schema requires a top-level session object containing `id`, `tool` and `entries`;
- ADR-015 describes v1.2 as NDJSON/JSONL with one event object per line and no required top-level fields;
- the README example is a top-level session object with an `entries` array.

Those are materially different serialization contracts. The policy core therefore retains internal audit records and does not invent event types or claim an AgentSON-compatible export. Add the adapter only after the canonical schema and serialization contract are reconciled and conformance-tested against the pinned schema.

## Not implemented

- tool adapters or arbitrary tool execution;
- OS process/container/VM isolation;
- filesystem, network, shell or device sandboxing;
- user-mode processes, syscalls, IPC and per-process address spaces;
- enforceable CPU-time, memory and wall-clock limits at the executor boundary;
- persistent audit storage or AgentSON export;
- model invocation, planning loops or autonomous agent orchestration.

## Failure handling

Timeouts, crashes, malformed requests, expired grants and quota exhaustion must fail closed. The policy core cannot contain a malicious or compromised executor. Until an isolated executor exists, do not use this library to authorise real filesystem, network, shell, credential or device operations.
