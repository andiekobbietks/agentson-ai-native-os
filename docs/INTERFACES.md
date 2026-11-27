# Component Interfaces

**Status:** Initial contracts; not implemented.

| Component | Responsibility | Boundary |
|---|---|---|
| Bootloader -> kernel | Boot info, memory map, modules | Validated pointer/length structure |
| Kernel -> user runtime | Process, memory, scheduling, IPC | Narrow syscalls/capabilities |
| Inference runtime -> model store | Read-only model and tokenizer | Versioned file format |
| Host policy core -> executor | Exact-scope authorization decision, request ID and output reservation | Executor must independently canonicalise resources and enforce OS isolation |\n| Workspace reader -> filesystem | Read one regular file below configured root using descriptor-relative no-follow opens | Read-only, exact-path, bounded output; no writes or directory listing |\n| Agent runtime -> tools | Typed requests and policy decisions | Allowlisted IPC/RPC |
| Runtime -> AgentSON | Execution lifecycle events | Versioned event schema; adapter deferred pending v1.2 contract reconciliation |
| Platform -> OIDL | Hardware capability/deployment description | Versioned declarative descriptor |
| Guest -> ivshmem model region | Read-only shared model bytes | Validated PCI BAR and bounded offsets |

## AgentSON
Use the existing AgentSON schema and versioning rules. Do not mint new canonical event names until checked against the actual specification. Keep the trace as an observability/interchange layer, not a substitute for access control.

## OIDL
Treat OIDL as optional metadata and capability description. It must not be required for boot and must never grant privileges merely by declaring a device.

## JITLLM
Audit the exact project, commit, build requirements and runtime assumptions before integration. A host Linux inference executable is not automatically safe or executable in ring 0.


## AgentSON compatibility note

The pinned AgentSON v1.2 schema and ADR-015 currently describe different serialization shapes. The runtime must not emit a guessed .agentson/JSONL format or invent primitives. See [Agent runtime](AGENT_RUNTIME.md) for the pinned references and integration gate.
