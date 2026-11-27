# ADR 0020: Read-only memory-mapped GGUF tensor reader

- **Status:** Accepted for host reference reader
- **Date:** 2026-11-27
- **Decision owners:** AgentSON project maintainers

## Context

The GGUF inspector validates the container and tensor directory, while the reference decoder accepts bytes-like tensor payloads. A file-backed API is needed to connect these stages without copying entire model files or tensor payloads into memory.

## Decision

Add a host-side `GGUFModel` reader that:
- opens a model file once and inspects it through the same seekable file handle;
- maps the file read-only;
- exposes validated tensor descriptors by name;
- streams decoded tensor values from a memory view;
- provides a bounded materializing helper for small tensors;
- refuses tensor types whose full payload extent is not validated;
- checks file identity, size and timestamps before and after access;
- requires active tensor iterators to be exhausted or closed before closing the mapping.

The shared parser is moved into `runtime/gguf_format.py`; `tools/gguf_inspect.py` becomes a thin CLI wrapper that re-exports the existing inspection API.

## Alternatives considered

- **Read the whole model into bytes:** rejected because model files may be large and this duplicates memory.
- **Reopen the file for each tensor:** rejected because it introduces avoidable file replacement and consistency races.
- **Guess unknown tensor extents:** rejected; unsupported layouts must fail closed.
- **Treat the reader as an inference engine:** rejected; it only exposes validated tensor bytes and decoded values.

## Consequences and limitations

The reader uses a read-only memory map and therefore requires the model file to remain immutable while open. Concurrent truncation may invalidate the mapping and is outside the guarantee. File metadata checks detect common modifications but do not provide cryptographic integrity or protect against a malicious host. The model path is trusted host configuration.

Only tensor types with validated extents and implemented dequantizers can be decoded. No tokenizer, matrix multiplication, attention, model execution, process isolation or kernel integration is included.

## Validation

Tests must cover same-handle stream inspection, tensor name lookup, supported and unsupported layouts, streaming and bounded materialization, iterator/mapping lifecycle, malformed files and file-change detection.

Passing these tests proves file-backed tensor access only, not executable inference.

## Follow-up

Add remaining quantisation formats, tokenizer metadata access and a reproducible host reference executor before considering guest integration.
