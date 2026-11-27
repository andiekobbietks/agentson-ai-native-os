# Reference Engineering Lessons

This project studies two public implementations without claiming their results as our own.

## Mitko Vasilev: qwen38-27b-baremetal-os
Repository: https://github.com/mitkox/qwen38-27b-baremetal-os  
Pinned reference commit: `6c43decc38aa8ea5fd22dba31360e8004601097d`  
Licence reported by GitHub: MIT. Verify file-level notices before adapting any source.

Observed engineering patterns from its README and build files:
- A tiny bootable kernel is separate from the much larger model weights.
- The large model is exposed through a read-only ivshmem PCI BAR rather than embedded in the boot image.
- Huge pages are used to reduce page-table overhead for large memory mappings.
- The model's hybrid recurrent/attention architecture requires a specialised state update, not a generic transformer-only path.
- SMP behaviour is tested across several virtual CPU counts.
- The author describes byte-level parity with a Linux implementation; this is an upstream claim until independently reproduced here.
- A host-side Linux inference path is used as a parity/reference target.
- Build targets and model provisioning are explicit in the Makefile.

## alesha-pro/llm.asm
Repository: https://github.com/alesha-pro/llm.asm  
Pinned commit: `48feccbfd57cb669440f31ff64958d95bb8b848e`  
Commit date: 2026-11-25. This is a verified immutable commit SHA; it is not a claim that this project has built it.

Observed engineering patterns:
- Shared assembly modules are reused across Linux and bare-metal builds with compile-time platform boundaries.
- A single Makefile exposes separate inference, bare-metal, training, check and ISO targets.
- Numerical kernels have independent tests and PyTorch/NumPy reference comparisons.
- Determinism is checked across thread counts.
- Model format versions are explicitly detected.
- Performance claims disclose hardware and workload details.

## Adopt as design principles, not copied implementation
1. Separate boot image from model payload.
2. Establish a small QEMU boot target before inference work.
3. Keep a host reference implementation for correctness comparison.
4. Verify numerical kernels independently.
5. Test SMP determinism across CPU counts.
6. Benchmark memory bandwidth, prefill and decode separately.
7. Record model/format/hardware/toolchain versions for every result.
8. Keep model parsing and agent tools outside the privileged kernel initially.

No Mitko or upstream assembly source has been copied into this repository by this documentation change.
