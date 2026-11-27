# ADR 0002: Keep model weights outside the kernel image

- Status: Accepted for research baseline
- Context: Mitko Vasilev's public Qwen 27B demonstration keeps a 33 KB kernel separate from 28.6 GB of weights and exposes the model through a read-only ivshmem PCI BAR. Embedding a model of that size in a boot image is impractical and couples boot to model provisioning.
- Decision: The kernel image and model payload are separate artefacts. The first prototype uses a host-side file or separately provisioned read-only backing region. ivshmem is an optional later experiment, not a boot dependency.
- Consequences: The kernel must validate device BAR metadata, mapping bounds, alignment and model headers. Model data remains untrusted. Smaller-page fallback and host-only inference remain available.
- Validation required: QEMU device tests, malformed model-header tests, bounds tests, read-only mapping verification and performance comparison.
