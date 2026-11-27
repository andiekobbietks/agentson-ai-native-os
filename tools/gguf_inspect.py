#!/usr/bin/env python3
"""Command-line entry point for the host-side GGUF inspector."""
from __future__ import annotations

import argparse
import json
import os
import sys

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runtime.gguf_format import (
    GGUFError,
    inspect_gguf,
    inspect_gguf_bytes,
    inspect_gguf_stream,
)

__all__ = ["GGUFError", "inspect_gguf", "inspect_gguf_bytes", "inspect_gguf_stream"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect GGUF v2/v3 metadata and tensor descriptors without loading weights."
    )
    parser.add_argument("model", help="path to a GGUF model file")
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    args = parser.parse_args(argv)
    try:
        result = inspect_gguf(args.model)
    except (OSError, GGUFError) as exc:
        print(f"gguf-inspect: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=None if args.compact else 2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
