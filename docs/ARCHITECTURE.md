# Architecture

## Initial target

x86-64 in QEMU. Keep hardware-specific code behind explicit architecture modules so additional targets do not contaminate the initial baseline.

## Layers

1. Boot and platform entry.
2. Kernel foundations: memory, exceptions, interrupts and scheduling.
3. Hardware abstraction and drivers.
4. Inference backend and model lifecycle.
5. Agent runtime with explicit capabilities and resource limits.
6. AgentSON event and provenance adapter.

## Design constraints

- Start with a minimal bootable kernel, not a broad feature set.
- Keep inference optional and independently testable.
- Treat model input, tool output and external data as untrusted.
- Require explicit capability grants for device, filesystem and network access.
- Keep AgentSON as an event interchange and audit layer, not as a kernel API or inference engine.
