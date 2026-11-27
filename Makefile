BUILD_DIR := build
ISO_ROOT := $(BUILD_DIR)/iso_root
KERNEL_ELF := $(BUILD_DIR)/kernel.elf
KERNEL_ISO := $(BUILD_DIR)/agentson-x86_64.iso
NASM ?= nasm
CC ?= gcc
LD ?= ld
QEMU ?= qemu-system-x86_64
PYTHON ?= python3
CFLAGS := -m64 -std=c11 -O2 -Wall -Wextra -Werror -ffreestanding -fno-stack-protector -fno-pic -fno-pie -fno-builtin -mno-red-zone -mgeneral-regs-only
LDFLAGS := -m elf_x86_64 -nostdlib -z max-page-size=0x1000 -T kernel/arch/x86_64/linker.ld
.PHONY: all clean check iso test toolchain-check
all: $(KERNEL_ISO)
$(BUILD_DIR):
	mkdir -p $@
$(BUILD_DIR)/boot.o: kernel/arch/x86_64/boot.asm | $(BUILD_DIR)
	$(NASM) -f elf64 $< -o $@
$(BUILD_DIR)/kernel.o: kernel/core/kernel.c | $(BUILD_DIR)
	$(CC) $(CFLAGS) -c $< -o $@
$(KERNEL_ELF): $(BUILD_DIR)/boot.o $(BUILD_DIR)/kernel.o kernel/arch/x86_64/linker.ld
	$(LD) $(LDFLAGS) $(BUILD_DIR)/boot.o $(BUILD_DIR)/kernel.o -o $@
	grub-file --is-x86-multiboot2 $@
$(KERNEL_ISO): $(KERNEL_ELF) grub/grub.cfg
	mkdir -p $(ISO_ROOT)/boot/grub
	cp $(KERNEL_ELF) $(ISO_ROOT)/boot/kernel.elf
	cp grub/grub.cfg $(ISO_ROOT)/boot/grub/grub.cfg
	grub-mkrescue -o $@ $(ISO_ROOT)
check: $(KERNEL_ELF)
	grub-file --is-x86-multiboot2 $(KERNEL_ELF)
	readelf -h $(KERNEL_ELF)
iso: $(KERNEL_ISO)
test: $(KERNEL_ISO)
	$(PYTHON) tests/boot/test_qemu_boot.py --qemu $(QEMU) --iso $(KERNEL_ISO)
toolchain-check:
	@command -v $(NASM) >/dev/null
	@command -v $(CC) >/dev/null
	@command -v $(LD) >/dev/null
	@command -v grub-file >/dev/null
	@command -v grub-mkrescue >/dev/null
	@command -v xorriso >/dev/null
	@command -v $(QEMU) >/dev/null
	@echo "Toolchain dependencies found."
clean:
	rm -rf $(BUILD_DIR)
