# AgentSON AI-Native OS

An independently developed, research-first AI-native bare-metal platform. Initial target: x86-64 in QEMU, using public source references and reproducible validation.

**Status:** Research scaffold and architecture baseline. No kernel implementation has yet been imported, built or boot-tested in this repository.

## Engineering direction

The project studies the public work of [Mitko Vasilev](https://github.com/mitkox/qwen38-27b-baremetal-os) and [alesha-pro](https://github.com/alesha-pro/llm.asm), but is an independent implementation. Their performance and correctness claims are upstream claims until reproduced here.

Key principles:
- Keep the bootable kernel small and independent of model-weight provisioning.
- Treat model weights as a separate, read-only payload; ivshmem is an optional later experiment, not a boot dependency.
- Validate memory maps, PCI BARs, model headers, offsets and sizes before access.
- Evaluate huge pages as a measured optimisation with smaller-page fallback.
- Establish a Linux/host reference path and compare outputs against it.
- Test numerical correctness and deterministic behaviour across CPU counts.
- Keep inference, model parsing and agent tools outside ring 0 in initial milestones.
- Emit versioned AgentSON execution records without treating observability as access control.

## Start here

- [AI contributor instructions](AGENTS.md)
- [Product requirements](docs/PRD.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Threat model](docs/THREAT_MODEL.md)
- [Boot design](docs/BOOT_DESIGN.md)
- [Memory model](docs/MEMORY_MODEL.md)
- [Inference design](docs/INFERENCE_DESIGN.md)
- [Agent runtime](docs/AGENT_RUNTIME.md)
- [Component interfaces](docs/INTERFACES.md)
- [Reference engineering lessons](docs/REFERENCE_ENGINEERING.md)
- [Windows/WSL2 setup](docs/WINDOWS_WSL2.md)
- [Validation plan](docs/VALIDATION.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

## Pinned research references

| Project | Pinned commit | Role |
|---|---|---|
| [alesha-pro/llm.asm](https://github.com/alesha-pro/llm.asm) | [48feccb](https://github.com/alesha-pro/llm.asm/commit/48feccbfd57cb669440f31ff64958d95bb8b848e) | Public base implementation and shared assembly/kernel work |
| [mitkox/qwen38-27b-baremetal-os](https://github.com/mitkox/qwen38-27b-baremetal-os) | [6c43dec](https://github.com/mitkox/qwen38-27b-baremetal-os/commit/6c43decc38aa8ea5fd22dba31360e8004601097d) | 27B hybrid model, ivshmem, huge-page and SMP design reference |

Both references are reported as MIT-licensed. Verify the exact file notices before adapting code. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). No upstream source has been copied into this repository by the documentation baseline work.

## Roadmap

1. **P0:** audit and reproduce pinned upstream build(s), recording toolchain, source inventory, logs and hashes.
2. **P1:** independently implement a minimal QEMU boot and serial smoke test.
3. **P2:** memory map, allocator, exceptions and interrupts.
4. **P3:** SMP and scoped device support.
5. **P4:** host-reference inference and model-format validation.
6. **P5:** isolated agent runtime and capability enforcement.
7. **P6:** AgentSON, OIDL and JITLLM adapters.
8. **P7:** fault injection, reproducibility, security and performance evaluation.

## Current validation status

| Capability | Status |
|---|---|
| Repository and architecture documentation | Present |
| Upstream revisions pinned | Yes; see research register |
| Upstream build reproduced locally | Not yet |
| Independent kernel source | Not implemented |
| QEMU boot test | Not implemented |
| Inference implementation | Not implemented |
| Agent runtime enforcement | Not implemented |
| AgentSON integration | Design only |
| CI | Documentation/metadata hygiene check added; kernel CI awaits source |

## Scope and safety

This is experimental OS research, not a production operating system or a hardened boundary against a malicious hypervisor, firmware or physical attacker. Use disposable virtual machines. Do not pass through host disks or expose unrestricted devices. Do not claim performance or correctness without reproducible evidence.

## Licence

The original project documentation and independently authored material are licensed under Apache-2.0. Third-party components retain their own licences and notices. Model weights and datasets have separate terms.
