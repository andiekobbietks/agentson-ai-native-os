#!/usr/bin/env python3
"""Boot the ISO in QEMU and assert the kernel's serial success marker."""
from __future__ import annotations
import argparse
import subprocess
import sys
def _as_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value

EXPECTED_MARKERS = (
    "BOOT_STAGE: long_mode_entered",
    "MULTIBOOT2_MAGIC: valid",
    "MULTIBOOT2_MEMORY_MAP: valid",
    "FRAME_ALLOC: valid",
    "PAGING: valid",
    "IDT: valid",
    "TIMER: valid",
    "TIMER_TICKS: ",
    "BOOT_OK: agentson-x86_64-timer-idt-exception",
    "EXCEPTION: page_fault",
    "EXCEPTION_TEST: page_fault_confirmed",
)
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qemu", default="qemu-system-x86_64")
    parser.add_argument("--iso", required=True)
    parser.add_argument("--timeout", type=int, default=15)
    args = parser.parse_args()
    command = [
        args.qemu, "-machine", "q35", "-cpu", "max", "-m", "512M",
        "-cdrom", args.iso, "-boot", "d", "-serial", "stdio",
        "-display", "none", "-monitor", "none", "-no-reboot",
        "-device",
        "isa-debug-exit,iobase=0xf4,iosize=0x04",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True,
                                timeout=args.timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        output = _as_text(exc.stdout) + _as_text(exc.stderr)
        print(output, file=sys.stderr)
        print("FAIL: QEMU did not reach debug-exit before timeout.",
              file=sys.stderr)
        return 1
    output = result.stdout + result.stderr
    print(output, end="" if output.endswith("\n") else "\n")
    missing = [marker for marker in EXPECTED_MARKERS if marker not in output]
    if missing:
        print(f"FAIL: missing serial markers: {missing}", file=sys.stderr)
        print(f"QEMU exit status: {result.returncode}", file=sys.stderr)
        return 1
    if result.returncode != 35:
        print(f"FAIL: expected exception debug-exit status 35, got {result.returncode}",
              file=sys.stderr)
        return 1
    print("PASS: x86-64 Multiboot2 kernel booted and validated boot info.")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
