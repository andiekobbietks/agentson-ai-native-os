# Windows development environment

Recommended workflow for Windows 10/11: Windows Terminal + WSL2 Ubuntu. Build and run QEMU inside Ubuntu; do not boot experimental kernels directly on the Windows host.

## Install
From Administrator Command Prompt:
```cmd
wsl --install -d Ubuntu
```
Restart if requested, launch Ubuntu once, create its Linux user, then:
```bash
sudo apt update
sudo apt install -y git make nasm binutils qemu-system-x86 xorriso grub-pc-bin grub-common python3 python3-venv
```

## Verify toolchain
```bash
git --version
make --version
nasm -v
ld --version
qemu-system-x86_64 --version
```

Keep working copies under `~/src` in the Linux filesystem for build performance. Use disposable QEMU guests, snapshots and no host disk passthrough.

## Current limitation
This repository does not yet contain a kernel Makefile or bootable kernel. These tools prepare the environment for the pinned upstream baseline audit and independent boot milestone; installation alone does not make this repository bootable.
