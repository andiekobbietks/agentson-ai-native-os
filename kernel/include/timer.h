#ifndef AGENTSON_TIMER_H
#define AGENTSON_TIMER_H

#include <stdint.h>

struct exception_frame;

void timer_init(uint32_t frequency_hz);
void timer_stop(void);
uint64_t timer_ticks(void);
struct exception_frame *irq_dispatch(struct exception_frame *frame);

#endif
