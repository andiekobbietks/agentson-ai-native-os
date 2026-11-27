# ADR 0019: Host-side GGUF tensor dequantization reference

- **Status:** Accepted for reference decoder prototype
- **Date:** 2026-11-27
- **Decision owners:** AgentSON project maintainers

## Context

The GGUF inspector validates tensor descriptors and supported tensor byte extents, but a model-format pipeline also needs independently testable tensor decoding. The project should establish byte-layout correctness before implementing matrix kernels or model execution.

## Decision

Implement a standard-library Python reference decoder for F32, F16, Q4_0, Q4_1, Q5_0, Q5_1, Q8_0 and Q8_1. Keep the tensor type/block-size table shared between the inspector and decoder and pin it to ggml commit `bb877c0c51f38c52ee2d5e41d58e3d0c20f3fed4`.

Provide a streaming iterator and a bounded materializing convenience function. Use deterministic golden vectors for each supported type. Reject unsupported codes, malformed block lengths, non-finite scales/values and materialization requests above the configured element limit.

Correct Q8_1 to 36 bytes per 32-element block (scale + auxiliary sum + 32 signed quant values).

## Alternatives considered

- **Implement a private model tensor format:** rejected because GGUF already defines the container and block type identifiers.
- **Copy upstream dequantization routines:** rejected; use the pinned upstream implementation as a format/algorithm reference and independently implement the decoder.
- **Implement K-quants and IQ formats immediately:** deferred until the simple block layouts are independently validated.
- **Treat dequantization as inference:** rejected; decoding weights is not matrix multiplication, attention, tokenization or generation.

## Consequences and limitations

This is host-side reference code, not a production-speed inference kernel. The iterator avoids an additional full output list, but callers still own the source buffer. The materializing helper defaults to a one-million-element cap. Q8_1's auxiliary sum is checked for finiteness but is not used to produce the dequantized values.

K-quants, IQ formats, tensor shape operations, matrix multiplication, attention, tokenizer support and model execution remain unimplemented. No model weights are included in the repository.

## Validation

Tests must include deterministic golden vectors for every supported type, correct low/high nibble and high-bit ordering, finite-value checks, malformed/truncated blocks, unsupported type codes and materialization limits. The GGUF inspector must independently validate Q8_1's 36-byte block extent.

Passing these tests proves only the documented byte decoding behaviour. It does not prove model correctness or executable inference.

## Follow-up

Implement K-quant formats required by target models, validate against independent reference outputs, then add tokenizer and host CPU reference execution before any kernel integration.
