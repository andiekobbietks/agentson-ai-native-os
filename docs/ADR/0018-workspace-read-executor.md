# ADR 0018: Read-only workspace file executor with descriptor-relative opens

- **Status:** Accepted for initial host-side tool prototype
- **Date:** 2026-11-27
- **Decision owners:** AgentSON project maintainers

## Context

The capability policy core can authorise exact resource scopes but does not execute tools or enforce filesystem boundaries. The first executor should demonstrate one useful operation without introducing shell access, writes, network access or general process execution.

A normal path check followed by a normal file open is vulnerable to path traversal and symlink time-of-check/time-of-use issues. The executor therefore needs descriptor-relative opens and fail-closed symlink handling.

## Decision

Implement one host-side read-only workspace tool. It accepts a relative path, constructs the exact resource identifier `workspace:/<relative-path>`, obtains a policy decision, and only then opens a regular file beneath a configured absolute workspace root.

On supported POSIX systems it must:
- reject absolute paths, empty components, dot/dot-dot segments, backslashes, wildcards and drive-style separators;
- open the configured root and every directory component with `O_DIRECTORY | O_NOFOLLOW`;
- open the final file with `O_NOFOLLOW` and non-blocking semantics;
- reject non-regular files and device changes across the workspace path;
- enforce the reserved output limit while reading;
- detect size/identity/timestamp changes during the read;
- settle or cancel the policy output reservation on every completion path.

The session and agent identity must come from trusted host runtime context, not from an untrusted tool payload.

## Alternatives considered

- **Shell-based file reading:** rejected because it grants an unnecessarily broad command-execution surface.
- **Path.resolve followed by open:** rejected because the path may change between validation and open.
- **General filesystem sandbox:** deferred until an isolated executor and OS-level boundary exist.
- **Workspace writes:** deferred until atomic-write, rollback, permissions and audit semantics are separately designed.

## Consequences and limitations

This is one read-only tool, not a general sandbox. It blocks traversal and symlink following for the opened path and rejects mount/device changes, but it does not establish process isolation, defend against a compromised host, distinguish hard links from ordinary workspace files, or make a mutable workspace immutable. The configured workspace root is trusted host configuration.

The tool is Linux/POSIX-specific and fails closed when required no-follow directory flags are unavailable. It does not provide writes, shell commands, network access, process creation or device access.

## Validation

Tests must cover exact grant binding, missing grants, traversal, absolute and malformed paths, final and intermediate symlinks, symlinked roots, directory rejection, output limits, empty files, nested files and budget settlement/cancellation.

A passing test suite validates only this read-only host tool. It does not prove general filesystem isolation.

## Follow-up

Add an isolated executor process with authenticated IPC, OS-enforced workspace confinement, resource limits and durable audit. Treat write, network and process capabilities as separate designs and ADRs.
