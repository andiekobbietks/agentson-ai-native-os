# ADR 0016: Use GGUF for the initial model-container inspection boundary

- **Status:** Accepted for host-side inspection prototype
- **Date:** 2026-11-27
- **Decision owners:** AgentSON project maintainers

## Context

The inference design needs a versioned, endian-explicit model container with metadata, tensor descriptors, offsets, alignment and quantisation identifiers. Defining a new private container before evaluating an established format would create unnecessary conversion and compatibility work.

GGUF is the model-container format used by GGML-based inference executors. Its specification defines a magic, versioned header, typed metadata, tensor descriptors, aligned tensor data and GGML tensor type codes.

## Decision

Use GGUF versions 2 and 3 in little-endian form as the initial model-inspection and host-reference interchange format. Pin the specification reference to ggml commit `bb877c0c51f38c52ee2d5e41d58e3d0c20f3fed4`.

The initial inspector is a host-side validation tool. It must:
- validate the magic, supported version, byte order and bounded header counts;
- validate UTF-8 strings, metadata keys, metadata types, arrays and duplicate keys;
- validate tensor names, dimensions, type codes, alignment and offsets;
- validate full tensor byte extents only for explicitly supported block layouts;
- reject malformed files and arithmetic/size values outside configured limits;
- avoid loading tensor payloads into memory.

## Alternatives considered

- **Private AgentSON model container:** rejected for the initial milestone because it would create a new conversion format without demonstrated need.
- **Parse only model filenames:** rejected because filenames do not prove internal structure or tensor bounds.
- **Adopt a full inference dependency immediately:** deferred until tensor reading, quantisation, tokenizer and reference-execution tests are established.

## Consequences and limitations

GGUF provides an existing interchange structure, but it does not make a model safe or guarantee that a particular architecture is executable. The inspector is not an inference engine, does not dequantize tensors, does not tokenize prompts and does not load a model into the kernel.

The current implementation fully validates byte extents only for F32, F16, Q4_0, Q4_1, Q5_0, Q5_1, Q8_0 and Q8_1. For other recognised GGML type codes it validates the tensor offset but cannot prove the complete tensor extent until the corresponding block layout is implemented and pinned. Big-endian files are rejected.

No GGML source code is copied by this decision. The project references the upstream format specification and keeps any future dependency evaluation separate from format parsing.

## Validation

The host test suite must cover valid metadata and tensor descriptors, Q8_0 block sizing, arrays, malformed/truncated headers, unsupported and big-endian versions, duplicate metadata, invalid booleans, bad alignment, misaligned offsets, invalid dimensions, unknown type codes, truncated tensor payloads and overlapping known tensor ranges.

A passing parser test validates only the implemented parser scope. It does not establish model execution, model correctness or safety against all malformed inputs.

## Follow-up

Add quantised tensor readers and dequantisation with independent golden vectors, then tokenizer validation and a deterministic host reference executor. Keep all model parsing and inference outside ring 0 until process isolation and resource limits exist.
