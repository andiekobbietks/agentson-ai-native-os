"""Pinned GGML tensor type identifiers and block layouts.

Reference: ggml commit bb877c0c51f38c52ee2d5e41d58e3d0c20f3fed4.
The table is independently maintained; no GGML implementation code is copied.
"""

# code: (name, elements per block, bytes per block)
GGML_TYPE_LAYOUTS = {
    0: ("F32", 1, 4),
    1: ("F16", 1, 2),
    2: ("Q4_0", 32, 18),
    3: ("Q4_1", 32, 20),
    6: ("Q5_0", 32, 22),
    7: ("Q5_1", 32, 24),
    8: ("Q8_0", 32, 34),
    9: ("Q8_1", 32, 36),
}

# Removed/reserved codes in the pinned ggml revision are excluded.
KNOWN_GGML_TYPE_CODES = frozenset(range(44)) - frozenset({4, 5, 31, 32, 33, 36, 37, 38})
