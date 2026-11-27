#include "scheduler.h"

#include <stddef.h>
#include <stdint.h>

#define SCHEDULER_TASK_COUNT 2u
#define TASK_STACK_SIZE 16384u

struct scheduler_task {
    struct exception_frame *saved_frame;
    uint8_t stack[TASK_STACK_SIZE] __attribute__((aligned(16)));
};

static struct scheduler_task tasks[SCHEDULER_TASK_COUNT];
static struct exception_frame *boot_frame;
static volatile uint64_t tick_count;
static volatile uint64_t task_counters[SCHEDULER_TASK_COUNT];
static uint32_t current_context;

static __attribute__((noreturn)) void task_exit(void)
{
    for (;;)
        __asm__ volatile ("hlt");
}

static __attribute__((noreturn)) void task_a(void)
{
    for (;;)
        ++task_counters[0];
}

static __attribute__((noreturn)) void task_b(void)
{
    for (;;)
        ++task_counters[1];
}

static void initialise_task(struct scheduler_task *task,
                            void (*entry)(void))
{
    uintptr_t stack_top = (uintptr_t)task->stack + TASK_STACK_SIZE;
    uintptr_t initial_rsp = stack_top - sizeof(uint64_t);
    *(uint64_t *)initial_rsp = (uint64_t)(uintptr_t)task_exit;

    struct exception_frame *frame =
        (struct exception_frame *)(initial_rsp - sizeof(*frame));
    uint64_t *words = (uint64_t *)frame;
    for (size_t i = 0u; i < sizeof(*frame) / sizeof(uint64_t); ++i)
        words[i] = 0u;

    frame->rip = (uint64_t)(uintptr_t)entry;
    frame->cs = 0x08u;
    frame->rflags = 0x202u;
    frame->rsp = initial_rsp;
    frame->ss = 0x10u;
    frame->vector = 32u;
    frame->error_code = 0u;
    task->saved_frame = frame;
}

void scheduler_init(void)
{
    boot_frame = NULL;
    tick_count = 0u;
    current_context = 0u;
    for (uint32_t i = 0u; i < SCHEDULER_TASK_COUNT; ++i) {
        task_counters[i] = 0u;
        tasks[i].saved_frame = NULL;
    }

    initialise_task(&tasks[0], task_a);
    initialise_task(&tasks[1], task_b);

}

struct exception_frame *scheduler_on_tick(struct exception_frame *frame)
{
    if (frame == NULL)
        return NULL;

    ++tick_count;

    if (current_context == 0u) {
        boot_frame = frame;
        current_context = 1u;
        return tasks[0].saved_frame;
    }

    if (current_context == 1u) {
        tasks[0].saved_frame = frame;
        current_context = 2u;
        return tasks[1].saved_frame;
    }

    tasks[1].saved_frame = frame;
    current_context = 0u;
    return boot_frame;
}

uint64_t scheduler_ticks(void)
{
    return tick_count;
}

uint64_t scheduler_task_counter(uint32_t task_id)
{
    if (task_id >= SCHEDULER_TASK_COUNT)
        return 0u;
    return task_counters[task_id];
}
