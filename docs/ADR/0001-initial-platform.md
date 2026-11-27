# ADR 0001: Initial Platform

- Status: Accepted for initial research phase
- Decision: x86-64 in QEMU is the first implementation target.
- Context: A narrow emulator target makes early boot and kernel work reproducible without requiring dedicated hardware.
- Consequences: Hardware support is initially limited; ARM64 and physical-machine validation are later milestones.
