# Component Interfaces

**Status:** Initial contracts; not implemented.

| Component | Responsibility | Boundary |
|---|---|---|
| Bootloader -> kernel | Boot info, memory map, modules | Validated pointer/length structure |
| Kernel -> user runtime | Process, memory, scheduling, IPC | Narrow syscalls/capabilities |
| Inference runtime -> model store | Read-only model and tokenizer | Versioned file format |
| Agent runtime -> tools | Typed requests and policy decisions | Allowlisted IPC/RPC |
| Runtime -> AgentSON | Execution lifecycle events | Versioned event schema |
| Platform -> OIDL | Hardware capability/deployment description | Versioned declarative descriptor |
| Guest -> ivshmem model region | Read-only shared model bytes | Validated PCI BAR and bounded offsets |

## AgentSON
Use the existing AgentSON schema and versioning rules. Do not mint new canonical event names until checked against the actual specification. Keep the trace as an observability/interchange layer, not a substitute for access control.

## OIDL
Treat OIDL as optional metadata and capability description. It must not be required for boot and must never grant privileges merely by declaring a device.

## JITLLM
Audit the exact project, commit, build requirements and runtime assumptions before integration. A host Linux inference executable is not automatically safe or executable in ring 0.
