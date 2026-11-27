"""Read-only, descriptor-relative workspace file executor.

The executor is intentionally Linux/POSIX-specific. It refuses to operate when
O_NOFOLLOW or O_DIRECTORY are unavailable, and it never follows user-supplied
symlinks or executes a tool outside the configured workspace.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
import stat

from .agent_policy import PolicyEngine, ToolRequest


@dataclass(frozen=True)
class ExecutionResult:
    allowed: bool
    reason: str
    request_id: str
    resource: str | None = None
    content: bytes | None = None


class WorkspaceReadExecutor:
    """A single read-only workspace capability; no writes or command execution."""

    def __init__(self, policy: PolicyEngine, root: str | os.PathLike[str]):
        root_path = os.fspath(root)
        if not os.path.isabs(root_path):
            raise ValueError("workspace root must be an absolute path")
        if not getattr(os, "O_NOFOLLOW", 0) or not getattr(os, "O_DIRECTORY", 0):
            raise RuntimeError("platform lacks required no-follow directory open flags")
        self._policy = policy
        self._root = root_path
        self._directory_flags = (
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        )
        self._file_flags = (
            os.O_RDONLY
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )

    @staticmethod
    def _components(relative_path: str) -> list[str]:
        if (
            not isinstance(relative_path, str)
            or not relative_path
            or len(relative_path) > 1000
            or relative_path.startswith("/")
            or "\\" in relative_path
            or "\x00" in relative_path
            or "*" in relative_path
            or "?" in relative_path
        ):
            raise ValueError("invalid relative workspace path")
        components = relative_path.split("/")
        if any(part in ("", ".", "..") or ":" in part for part in components):
            raise ValueError("invalid relative workspace path")
        return components

    def _open_file(self, components: list[str]) -> tuple[int, int]:
        root_fd = os.open(self._root, self._directory_flags)
        try:
            root_stat = os.fstat(root_fd)
            if not stat.S_ISDIR(root_stat.st_mode):
                raise OSError("workspace root is not a directory")

            parent_fd = root_fd
            owns_parent = False
            try:
                for component in components[:-1]:
                    next_fd = os.open(
                        component,
                        self._directory_flags,
                        dir_fd=parent_fd,
                    )
                    next_stat = os.fstat(next_fd)
                    if not stat.S_ISDIR(next_stat.st_mode) or next_stat.st_dev != root_stat.st_dev:
                        os.close(next_fd)
                        raise OSError("workspace path crosses a directory or device boundary")
                    if owns_parent:
                        os.close(parent_fd)
                    parent_fd = next_fd
                    owns_parent = True

                file_fd = os.open(
                    components[-1],
                    self._file_flags,
                    dir_fd=parent_fd,
                )
                return file_fd, root_stat.st_dev
            finally:
                if owns_parent:
                    os.close(parent_fd)
        finally:
            os.close(root_fd)

    def read_file(
        self,
        *,
        request_id: str,
        session_id: str,
        agent_id: str,
        relative_path: str,
        output_limit_bytes: int,
        now_ms: int,
        completed_at_ms: int | None = None,
    ) -> ExecutionResult:
        """Authorize and read one regular file without following symlinks.

        Session and agent identifiers must come from the trusted host runtime,
        not from an untrusted tool payload.
        """
        if type(now_ms) is not int or now_ms < 0:
            return ExecutionResult(False, "invalid_request_or_resource_path", request_id)
        if completed_at_ms is not None and (
            type(completed_at_ms) is not int or completed_at_ms < now_ms
        ):
            return ExecutionResult(False, "invalid_request_or_resource_path", request_id)

        try:
            components = self._components(relative_path)
            resource = "workspace:/" + "/".join(components)
            request = ToolRequest(
                request_id=request_id,
                session_id=session_id,
                agent_id=agent_id,
                capability="workspace.read",
                resource=resource,
                output_limit_bytes=output_limit_bytes,
            )
        except ValueError:
            return ExecutionResult(False, "invalid_request_or_resource_path", request_id)

        decision = self._policy.authorize(request, now_ms)
        if not decision.allowed:
            return ExecutionResult(False, decision.reason, request_id, resource)

        file_fd = None
        try:
            file_fd, root_device = self._open_file(components)
            before = os.fstat(file_fd)
            if not stat.S_ISREG(before.st_mode):
                self._policy.cancel(request_id, now_ms)
                return ExecutionResult(False, "not_regular_file", request_id, resource)
            if before.st_dev != root_device:
                self._policy.cancel(request_id, now_ms)
                return ExecutionResult(False, "resource_boundary_violation", request_id, resource)
            if before.st_size > output_limit_bytes:
                self._policy.cancel(request_id, now_ms)
                return ExecutionResult(False, "output_limit_exceeded", request_id, resource)

            content = bytearray()
            while True:
                remaining_with_probe = output_limit_bytes - len(content) + 1
                chunk = os.read(file_fd, min(65536, remaining_with_probe))
                if not chunk:
                    break
                content.extend(chunk)
                if len(content) > output_limit_bytes:
                    self._policy.cancel(request_id, now_ms)
                    return ExecutionResult(False, "output_limit_exceeded", request_id, resource)

            after = os.fstat(file_fd)
            if (
                before.st_dev != after.st_dev
                or before.st_ino != after.st_ino
                or before.st_size != after.st_size
                or before.st_mtime_ns != after.st_mtime_ns
                or before.st_ctime_ns != after.st_ctime_ns
            ):
                self._policy.cancel(request_id, now_ms)
                return ExecutionResult(False, "resource_changed_during_read", request_id, resource)

            settled_at = now_ms if completed_at_ms is None else completed_at_ms
            if not self._policy.settle(request_id, len(content), settled_at):
                return ExecutionResult(False, "policy_settlement_failed", request_id, resource)
            return ExecutionResult(True, "read", request_id, resource, bytes(content))
        except OSError:
            self._policy.cancel(request_id, now_ms)
            return ExecutionResult(False, "resource_unavailable", request_id, resource)
        finally:
            if file_fd is not None:
                os.close(file_fd)
