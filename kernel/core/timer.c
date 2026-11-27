#include "timer.h"
#include "idt.h"
#include "scheduler.h"

#include <stddef.h>

#include <stdint.h>

#define PIC_MASTER_COMMAND 0x20u
#define PIC_MASTER_DATA 0x21u
#define PIC_SLAVE_COMMAND 0xA0u
#define PIC_SLAVE_DATA 0xA1u
#define PIT_COMMAND 0x43u
#define PIT_CHANNEL0 0x40u
#define PIT_INPUT_HZ 1193182u

static volatile uint64_t ticks;

static inline void outb(uint16_t port, uint8_t value)
{
    __asm__ volatile ("outb %0, %1" : : "a"(value), "Nd"(port));
}

void timer_init(uint32_t frequency_hz)
{
    if (frequency_hz == 0u || frequency_hz > PIT_INPUT_HZ)
        frequency_hz = 100u;

    /* Remap the legacy PIC to vectors 0x20–0x2F. */
    outb(PIC_MASTER_COMMAND, 0x11u);
    outb(PIC_SLAVE_COMMAND, 0x11u);
    outb(PIC_MASTER_DATA, 0x20u);
    outb(PIC_SLAVE_DATA, 0x28u);
    outb(PIC_MASTER_DATA, 0x04u);
    outb(PIC_SLAVE_DATA, 0x02u);
    outb(PIC_MASTER_DATA, 0x01u);
    outb(PIC_SLAVE_DATA, 0x01u);

    /* Unmask only IRQ0 on the master; mask all slave IRQs. */
    outb(PIC_MASTER_DATA, 0xFEu);
    outb(PIC_SLAVE_DATA, 0xFFu);

    uint32_t divisor = PIT_INPUT_HZ / frequency_hz;
    if (divisor == 0u || divisor > 0xFFFFu)
        divisor = 0xFFFFu;

    outb(PIT_COMMAND, 0x36u);
    outb(PIT_CHANNEL0, (uint8_t)(divisor & 0xFFu));
    outb(PIT_CHANNEL0, (uint8_t)((divisor >> 8) & 0xFFu));

    ticks = 0u;
    __asm__ volatile ("sti");
}

void timer_stop(void)
{
    __asm__ volatile ("cli");
    outb(PIC_MASTER_DATA, 0xFFu);
    outb(PIC_SLAVE_DATA, 0xFFu);
}

uint64_t timer_ticks(void)
{
    return ticks;
}

struct exception_frame *irq_dispatch(struct exception_frame *frame)
{
    if (frame != NULL && frame->vector == 32u)
        ++ticks;

    /* Acknowledge before selecting the next saved interrupt frame. */
    outb(PIC_MASTER_COMMAND, 0x20u);
    return scheduler_on_tick(frame);
}
