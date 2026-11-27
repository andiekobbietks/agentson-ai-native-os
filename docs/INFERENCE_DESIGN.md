# Inference Design

**Status:** Host-side GGUF inspection and bounded tensor dequantization are implemented for F32, F16, Q4_0, Q4_1, Q5_0, Q5_1, Q8_0 and Q8_1. Tokenizer, matrix kernels and model execution are not implemented.

## Lessons from the public assembly projects

- Keep model-format conversion offline and version the resulting binary format.
- Separate the inference engine from the bare-metal boot path.
- Reuse mathematical kernels only after independent correctness tests.
- Verify outputs against an independent reference implementation.
- Measure decode and prefill separately, and publish hardware, model, quantisation, prompt, token count and thread count.
- Treat CPU SIMD support as a runtime capability, not an assumption.
- Make multi-thread scheduling deterministic where practical and test across thread counts.

## Architecture boundary

The first inference milestone is a host/Linux user-space executable. The bare-metal kernel boots independently and provides no model-loading or inference syscall yet. Later, a user-mode runtime or dedicated guest service may use validated model storage and IPC. Ring-0 inference is not a prerequisite for an AI-native OS.

Model files, tokenizer assets and metadata are untrusted input. Parsing and tensor validation remain outside the privileged kernel until process isolation, memory ownership and resource quotas exist.

## Model container

Use GGUF v2/v3 little-endian as the initial model-inspection and host-reference interchange format. The implementation is based on the pinned [GGUF specification](https://github.com/ggml-org/ggml/blob/bb877c0c51f38c52ee2d5e41d58e3d0c20f3fed4/docs/gguf.md), not copied GGML source code.

The host-side inspector currently validates:
- GGUF magic, version and byte order;
- bounded header counts and UTF-8 strings;
- metadata keys, scalar types, arrays and duplicate-key rejection;
- tensor names, dimensions, recognised GGML type codes and alignment;
- tensor data extents for F32, F16, Q4_0, Q4_1, Q5_0, Q5_1, Q8_0 and Q8_1;
- file bounds and overlapping ranges for tensor types with implemented block layouts.

For other recognised GGML tensor type codes, the inspector validates the offset but does not claim full tensor-extent validation. Big-endian GGUF is rejected. These limits are deliberate and visible in the tool output.

## Tensor dequantization

`runtime/gguf_types.py` is the shared, pinned block-layout table used by both the inspector and decoder. `runtime/gguf_tensor.py` provides:
- `iter_dequantized`: a block-at-a-time iterator over a bytes-like buffer;
- `dequantize_tensor`: a convenience materializer with a default one-million-element limit.

The reference decoder currently supports:
- F32 and F16 scalar payloads;
- Q4_0 and Q4_1 nibble-packed 32-element blocks;
- Q5_0 and Q5_1 blocks with packed high bits;
- Q8_0 signed 8-bit blocks;
- Q8_1 signed 8-bit blocks with its auxiliary sum field.

Q8_1 is 36 bytes per 32-element block: two-byte scale, two-byte auxiliary sum and 32 signed quant values. The inspector's block-size table was corrected to this layout and has a dedicated bounds test. The decoder checks the auxiliary sum is finite but uses the scale and signed quant values for dequantization.

The decoder rejects truncated blocks, unsupported type codes and non-finite scales/values. It does not implement K-quants (Q2_K through Q6_K), IQ formats, tensor shape operations, matrix multiplication, attention, tokenization or model execution. The iterator avoids an additional full-size output list, but the caller still owns the source buffer.

## Implementation sequence

1. **Container inspection:** bounded GGUF header, metadata and tensor-directory parsing with malformed-file tests. Complete for the documented scope.
2. **Tensor decoding:** host reference dequantization for eight scalar/block types with deterministic golden vectors. K-quants and further type coverage remain.
3. **Tokenizer:** validate vocabulary, merges, special tokens and tokenizer configuration from model metadata.
4. **Host reference executor:** implement a small deterministic CPU path and compare outputs against a pinned independent runtime.
5. **Guest integration:** only after process isolation, model backing, IPC, memory mapping and resource limits exist.

## Explicit non-goals of the current tools

The inspector and decoder do not load a model, execute matrix multiplication, perform attention, generate tokens or run Qwen. A successful tensor dequantization test is not evidence that a model can be executed or that its weights are trustworthy.
