#ifndef AGENTSON_SCHEDULER_H
#define AGENTSON_SCHEDULER_H

#include <stdint.h>
#include "idt.h"

void scheduler_init(void);
struct exception_frame *scheduler_on_tick(struct exception_frame *frame);
uint64_t scheduler_ticks(void);
uint64_t scheduler_task_counter(uint32_t task_id);

#endif
