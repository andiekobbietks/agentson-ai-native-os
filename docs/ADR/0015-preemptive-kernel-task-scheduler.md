# ADR 0015: Bootstrap preemptive task switching

- **Status:** Accepted for two-task QEMU prototype
- **Date:** 2026-11-27
- **Decision owners:** AgentSON project maintainers

## Context

The kernel has a working single-core PIT/PIC IRQ0 path and a saved interrupt-frame layout. A minimal task-switching experiment is needed to establish whether the kernel can resume distinct execution contexts from timer interrupts before introducing a more capable scheduler.

This is a research milestone. It is not a process model, userspace implementation or security boundary.

## Decision

For the next bootstrap milestone, implement a fixed two-task, ring-0, round-robin context switch by saving the existing interrupt frame on each task's kernel stack and returning the next saved frame from the IRQ dispatcher.

The experiment must:
- model the complete 64-bit interrupt return frame, including the hardware-saved RSP and SS slots that IRETQ restores in long mode;
- keep the task count fixed at two;
- use statically allocated, bounded kernel stacks;
- switch only on the existing IRQ0 path;
- demonstrate that both task entry points execute and that the boot context resumes;
- stop and mask the timer before running the existing controlled page-fault test;
- run only in the disposable QEMU test target.

## Alternatives considered

- **Cooperative yield:** simpler, but does not demonstrate timer-driven preemption.
- **Full scheduler with priorities and queues:** premature before context-switch invariants, stack ownership and interrupt return are validated.
- **Ring-3 processes:** deferred because TSS, privilege transitions, syscall entry, per-process address spaces and isolation are not implemented.

## Consequences and limitations

This is a controlled context-switch experiment, not a production scheduler. Tasks run in ring 0 with shared address space and unrestricted kernel privilege. There is no FPU/SIMD context management, task lifecycle, blocking/wakeup, priorities, scheduler lock, stack guard, per-task resource accounting, SMP, TSS/IST stack, userspace or isolation between tasks.

The task stacks are static and the task count is fixed. The PIT/PIC implementation remains a legacy single-core test path. No task may be treated as untrusted.

## Validation

The QEMU test must assert:
- the scheduler initialises;
- timer ticks advance;
- both task counters become non-zero;
- the boot context resumes and the timer is masked;
- the existing expected supervisor page fault is still diagnosed;
- QEMU exits with the expected debug-exit status.

GitHub Actions run #46 passed the QEMU test at commit 81ebc861305c5defa6d70f15537f233303d54b80. The serial output confirmed nine timer ticks, non-zero counters for both tasks, boot-context resumption, and the expected page-fault diagnostic. This validates only the fixed two-task QEMU prototype; it does not establish SMP safety or production readiness.

## Follow-up

Before expanding scheduling, define task state and lifecycle, stack ownership/guarding, interrupt nesting policy, FPU/SIMD policy, timer abstraction, and the locking model. SMP and userspace require separate ADRs and independent validation.
