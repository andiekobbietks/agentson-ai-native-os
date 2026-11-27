# Third-party notices

No third-party source code has been copied into this repository at this revision.

## Reference projects (not included as code)
- `alesha-pro/llm.asm`: https://github.com/alesha-pro/llm.asm — MIT; pinned reference commit `48feccbfd57cb669440f31ff64958d95bb8b848e`.
- `mitkox/qwen38-27b-baremetal-os`: https://github.com/mitkox/qwen38-27b-baremetal-os — GitHub reports MIT; pinned reference commit `6c43decc38aa8ea5fd22dba31360e8004601097d`.

These are research references only. If code is later adapted, retain applicable copyright and licence notices, identify every changed file, and update this register. Model weights and datasets have separate licensing terms.


## GGUF format specification reference

- **Project:** ggml
- **References:** [GGUF specification](https://github.com/ggml-org/ggml/blob/bb877c0c51f38c52ee2d5e41d58e3d0c20f3fed4/docs/gguf.md) and [GGML tensor type enum](https://github.com/ggml-org/ggml/blob/bb877c0c51f38c52ee2d5e41d58e3d0c20f3fed4/include/ggml.h)
- **Pinned revision:** bb877c0c51f38c52ee2d5e41d58e3d0c20f3fed4
- **Use:** format specification, tensor-layout and dequantization-algorithm references for independently authored host-side GGUF inspection and decoding.\n- **Additional references:** [GGML block layouts](https://github.com/ggml-org/ggml/blob/bb877c0c51f38c52ee2d5e41d58e3d0c20f3fed4/src/ggml-common.h) and [GGML dequantization routines](https://github.com/ggml-org/ggml/blob/bb877c0c51f38c52ee2d5e41d58e3d0c20f3fed4/src/ggml-quants.c).
- **Source code copied:** none.
- **Dependency:** none; the inspector uses the Python standard library.

The upstream repository is MIT-licensed at the pinned revision. The specification is referenced for compatibility; this repository does not redistribute GGML implementation code or model weights.
