#include "idt.h"
#include "serial.h"

#include <stddef.h>

#include <stdint.h>

#define QEMU_EXIT_PORT 0xF4u
#define EXPECTED_PAGE_FAULT_ADDRESS 0x80000000ull

static inline uint64_t read_cr2(void)
{
    uint64_t value;
    __asm__ volatile ("mov %%cr2, %0" : "=r"(value));
    return value;
}

static __attribute__((noreturn)) void exception_exit(uint32_t code)
{
    __asm__ volatile ("outl %0, %1" : : "a"(code), "Nd"((uint16_t)QEMU_EXIT_PORT));
    for (;;)
        __asm__ volatile ("cli; hlt");
}

void exception_dispatch(struct exception_frame *frame)
{
    if (frame == NULL)
        exception_exit(0x12u);

    if (frame->vector == 14u) {
        const uint64_t fault_address = read_cr2();
        serial_write("EXCEPTION: page_fault\n");
        serial_write("EXCEPTION_ERROR_CODE: ");
        serial_write_hex64(frame->error_code);
        serial_write("\n");
        serial_write("CR2: ");
        serial_write_hex64(fault_address);
        serial_write("\n");

        if (fault_address == EXPECTED_PAGE_FAULT_ADDRESS &&
            frame->error_code == 0u) {
            serial_write("EXCEPTION_TEST: page_fault_confirmed\n");
            exception_exit(0x11u);
        }
    } else {
        serial_write("EXCEPTION: unexpected\n");
        serial_write("VECTOR: ");
        serial_write_hex64(frame->vector);
        serial_write("\n");
        serial_write("ERROR_CODE: ");
        serial_write_hex64(frame->error_code);
        serial_write("\n");
    }

    exception_exit(0x12u);
}
