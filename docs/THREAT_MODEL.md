# Threat Model

**Status:** Initial design; not a completed security assessment.

## Assets
- Kernel integrity and control flow.
- Model weights and tokenizer assets.
- Agent credentials and delegated capabilities.
- Host/guest shared-memory contents.
- Execution traces and provenance records.
- User data processed by inference or tools.

## Trust boundaries
1. Host OS and hypervisor to guest kernel.
2. Bootloader/firmware to kernel entry.
3. Kernel to inference runtime.
4. Agent runtime to tools, filesystems and network.
5. ivshmem/device memory to guest consumers.
6. AgentSON event producer to storage/export consumers.

## Principal threats and controls

| Threat | Initial control direction | Required evidence |
|---|---|---|
| Malformed model or tokenizer | Parse in unprivileged process; strict bounds checks | Fuzz and malformed-fixture tests |
| Agent prompt injection | Treat content as data; tool allowlists and confirmation gates | Denied-tool tests |
| Privilege escalation | Keep inference/tools out of ring 0; host policy core only authorises exact scopes and does not execute tools | Policy negative tests; process isolation and executor boundary not implemented |
| Shared-memory corruption | Read-only mapping where possible; validate BAR size/offsets; bounds-check all reads | Device emulation and corruption tests |
| DMA/device compromise | No unrestricted DMA initially; IOMMU policy before passthrough | Threat review and IOMMU tests |
| Resource exhaustion | Host policy core enforces session action/output budgets and deadlines; executor-level CPU/memory/time limits remain required | Policy unit tests pass; executor enforcement not implemented |
| Trace tampering | Hash chaining/signatures only with defined key lifecycle; external anchoring | Tamper/replay tests |
| Malicious or stale firmware | Document boot trust assumptions; Secure Boot measured-boot work is future scope | Platform-specific verification |

## Explicit non-goals
The first milestones do not provide a hardened security boundary against a malicious hypervisor, compromised firmware, physical attacks or arbitrary hostile PCI devices.

## Security invariants
- No model input may directly select arbitrary kernel memory addresses.
- No agent receives ambient filesystem, network or device access.
- Every cross-boundary buffer has a checked length and ownership rule.
- Failure to validate a capability or resource budget must fail closed.
- Audit records must distinguish observed facts from inferred or user-supplied claims.
