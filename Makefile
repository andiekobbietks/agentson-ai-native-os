BUILD_DIR := build
ISO_ROOT := $(BUILD_DIR)/iso_root
KERNEL_ELF := $(BUILD_DIR)/kernel.elf
KERNEL_ISO := $(BUILD_DIR)/agentson-x86_64.iso
NASM ?= nasm
CC ?= gcc
LD ?= ld
QEMU ?= qemu-system-x86_64
PYTHON ?= python3
CFLAGS := -m64 -std=c11 -O2 -Wall -Wextra -Werror -ffreestanding -fno-stack-protector -fno-pic -fno-pie -fno-builtin -mno-red-zone -mgeneral-regs-only -Ikernel/include
LDFLAGS := -m elf_x86_64 -nostdlib -z max-page-size=0x1000 -T kernel/arch/x86_64/linker.ld
.PHONY: all clean check iso test test-unit test-model-format test-agent-policy toolchain-check
all: $(KERNEL_ISO)
$(BUILD_DIR):
	mkdir -p $@
$(BUILD_DIR)/boot.o: kernel/arch/x86_64/boot.asm | $(BUILD_DIR)
	$(NASM) -f elf64 $< -o $@
$(BUILD_DIR)/kernel.o: kernel/core/kernel.c kernel/include/multiboot2.h kernel/include/frame_allocator.h kernel/include/paging.h kernel/include/idt.h kernel/include/serial.h kernel/include/timer.h kernel/include/scheduler.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -c $< -o $@
$(BUILD_DIR)/multiboot2.o: kernel/core/multiboot2.c kernel/include/multiboot2.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -c $< -o $@
$(BUILD_DIR)/frame_allocator.o: kernel/mm/frame_allocator.c kernel/include/frame_allocator.h kernel/include/multiboot2.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -c $< -o $@
$(BUILD_DIR)/paging.o: kernel/mm/paging.c kernel/include/paging.h kernel/include/frame_allocator.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -c $< -o $@
$(BUILD_DIR)/serial.o: kernel/core/serial.c kernel/include/serial.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -c $< -o $@
$(BUILD_DIR)/idt.o: kernel/arch/x86_64/idt.c kernel/include/idt.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -c $< -o $@
$(BUILD_DIR)/exception.o: kernel/arch/x86_64/exception.c kernel/include/idt.h kernel/include/serial.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -c $< -o $@
$(BUILD_DIR)/interrupts.o: kernel/arch/x86_64/interrupts.asm | $(BUILD_DIR)
	$(NASM) -f elf64 $< -o $@
$(BUILD_DIR)/timer.o: kernel/core/timer.c kernel/include/timer.h kernel/include/idt.h kernel/include/scheduler.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -c $< -o $@
$(BUILD_DIR)/scheduler.o: kernel/core/scheduler.c kernel/include/scheduler.h kernel/include/idt.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -c $< -o $@
$(KERNEL_ELF): $(BUILD_DIR)/boot.o $(BUILD_DIR)/kernel.o $(BUILD_DIR)/multiboot2.o $(BUILD_DIR)/frame_allocator.o $(BUILD_DIR)/paging.o $(BUILD_DIR)/serial.o $(BUILD_DIR)/idt.o $(BUILD_DIR)/exception.o $(BUILD_DIR)/interrupts.o $(BUILD_DIR)/timer.o $(BUILD_DIR)/scheduler.o kernel/arch/x86_64/linker.ld
	$(LD) $(LDFLAGS) $(BUILD_DIR)/boot.o $(BUILD_DIR)/kernel.o $(BUILD_DIR)/multiboot2.o $(BUILD_DIR)/frame_allocator.o $(BUILD_DIR)/paging.o $(BUILD_DIR)/serial.o $(BUILD_DIR)/idt.o $(BUILD_DIR)/exception.o $(BUILD_DIR)/interrupts.o $(BUILD_DIR)/timer.o $(BUILD_DIR)/scheduler.o -o $@
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
test-unit: | $(BUILD_DIR)
	$(CC) -std=c11 -Wall -Wextra -Werror -Ikernel/include kernel/core/multiboot2.c kernel/mm/frame_allocator.c tests/unit/test_memory.c -o $(BUILD_DIR)/test_memory
	$(BUILD_DIR)/test_memory
test-model-format:
	$(PYTHON) -m unittest discover -s tests/unit -p 'test_gguf_inspect.py' -v
test-agent-policy:
	$(PYTHON) -m unittest discover -s tests/unit -p 'test_agent_policy.py' -v
test: $(KERNEL_ISO) test-unit test-model-format test-agent-policy
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
