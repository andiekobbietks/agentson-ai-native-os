# Research and Source Register

## Public implementation reference: alesha-pro/llm.asm
- Repository: https://github.com/alesha-pro/llm.asm
- Pinned commit: `48feccbfd57cb669440f31ff64958d95bb8b848e`
- Commit URL: https://github.com/alesha-pro/llm.asm/commit/48feccbfd57cb669440f31ff64958d95bb8b848e
- Commit date: 2026-11-25
- Relevant path: `02-baremetal-os/`; root Makefile and shared NASM modules.
- GitHub reports MIT. The pinned commit changes the FAST_Q8 INT8xINT8 AVX2/F16C path, FP16 scale model format, parallel GQA and tests.
- Status: immutable commit existence and metadata verified; build has NOT been reproduced in this project.

## Public implementation reference: Mitko Vasilev
- Repository: https://github.com/mitkox/qwen38-27b-baremetal-os
- Pinned commit: `6c43decc38aa8ea5fd22dba31360e8004601097d`
- Commit URL: https://github.com/mitkox/qwen38-27b-baremetal-os/commit/6c43decc38aa8ea5fd22dba31360e8004601097d
- Commit date: 2026-11-26
- GitHub reports MIT; upstream LICENSE attributes the original project to Alexey Fateev (alesha-pro). Preserve all notices if adapting any files.
- Relevant path: `04-qwen38-27b-os/`, root Makefile, `shared/qwen35.asm`, `shared/qwen35.inc`, `scripts/verify_os27.py`.
- Status: README, Makefile, repository metadata and tree inspected; no local build or benchmark reproduced here.
- Engineering lessons are documented in [REFERENCE_ENGINEERING.md](REFERENCE_ENGINEERING.md).

## Architectural reference only
- https://github.com/tomstuhl/agentos
- Full kernel source is described as restricted to selected design partners/core contributors.
- Do not make this project depend on unavailable source.

## User's related projects
- NetBird fork: https://github.com/andiekobbietks/netbird (networking/security reference, not the bare-metal OS implementation).
- JITLLM: https://github.com/andiekobbietks/jitllm
- OIDL: https://github.com/andiekobbietks/OIDL
- AgentSON: https://github.com/andiekobbietks/AgentSON

These are separate projects. Audit their exact source, interfaces and licences before integration. The NetBird fork is not Mitko's OS fork.

## Source reuse gate
Before copying/adapting any source: record repository, immutable commit, exact file paths, copyright headers, licence, modifications and tests in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md). Do not import whole upstream repositories blindly. Model weights, tokenizer assets, datasets and screenshots may have separate licences.
