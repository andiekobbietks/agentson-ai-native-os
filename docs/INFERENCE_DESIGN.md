# Inference Design

**Status:** Proposed; implementation pending.

## Lessons from the public assembly projects
- Keep model-format conversion offline and version the resulting binary format.
- Separate the inference engine from the bare-metal boot path.
- Reuse mathematical kernels only after independent correctness tests.
- Verify outputs against an independent reference implementation.
- Measure decode and prefill separately, and publish hardware, model, quantisation, prompt, token count and thread count.
- Treat CPU SIMD support as a runtime capability, not an assumption.
- Make multi-thread scheduling deterministic where practical and test across thread counts.

## Architecture boundary
The first inference milestone should be a host/Linux user-space executable that shares well-defined model and kernel code where practical. The bare-metal kernel milestone should boot independently before any inference integration. Later, add a user-mode runtime or dedicated guest service. Ring-0 inference is not a prerequisite for an AI-native OS.

## Model format
Define a versioned, endian-explicit, bounds-checked container with:
- magic and format version;
- architecture/config metadata;
- tensor directory and data types;
- alignment and offsets;
- tokenizer metadata;
- quantisation scheme and scale representation;
- integrity digest;
- explicit maximum sizes.

Never trust offsets, dimensions or tensor counts from the file. Validate arithmetic for overflow before mapping or reading.
