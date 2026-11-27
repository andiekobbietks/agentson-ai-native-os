# Instructions for AI and human contributors

## Project truth
This repository began as a research scaffold and now contains an experimental QEMU-bootable x86-64 kernel with memory-management, exception, timer and two-task ring-0 scheduling prototypes. A host-side, bounds-checked GGUF inspector and reference dequantizer for eight tensor types, deny-by-default capability policy core and one read-only workspace-file executor are present; model execution, general tool execution and process isolation remain unimplemented. Native model inference, userspace and an agent runtime are not implemented. Do not describe a feature as implemented, bootable, secure, deterministic, or benchmarked unless code and reproducible evidence exist in this repository.

## Engineering rules
- Read the relevant architecture decision records and source register before changing platform choices.
- Keep upstream reference checkouts separate from this repository. Never copy an entire upstream project wholesale.
- Before adapting any third-party file, record its exact source URL, commit, path, licence, copyright notices, modifications and rationale in `THIRD_PARTY_NOTICES.md`.
- Do not assume a repository-level licence covers model weights, datasets, assets, generated files or dependencies.
- Keep the first kernel small. Inference, model parsing, networking and agent tools should initially run outside the privileged kernel.
- Treat model files, prompts, tool output, device input and host-shared memory as untrusted.
- Require explicit resource limits and capability grants for every agent operation.
- Prefer deterministic tests, fixed fixtures and independent reference implementations.
- Never fabricate benchmark numbers or claim upstream benchmarks as results of this project.

## Change workflow
1. State the intended behaviour and threat boundary.
2. Add or update tests with the change.
3. Run the documented checks and record exact output.
4. Update architecture docs and the validation matrix.
5. Keep changes small enough to review.
