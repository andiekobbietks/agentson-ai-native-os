"""Deny-by-default capability policy core for host-side agent execution.

This module decides whether a proposed tool operation may start. It does not
execute tools, create OS sandboxes, enforce filesystem/network isolation, or
export AgentSON traces. The executor must enforce the same resource boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import threading


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_CAPABILITY = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


def _require_identifier(value: str, field: str) -> None:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"{field} must be a non-empty bounded identifier")


def _require_scope(value: str, field: str) -> None:
    if not isinstance(value, str) or not value or len(value) > 1024:
        raise ValueError(f"{field} must be a non-empty bounded string")
    if "*" in value or "?" in value:
        raise ValueError(f"{field} must be exact; wildcard scopes are not supported")


@dataclass(frozen=True)
class CapabilityGrant:
    grant_id: str
    session_id: str
    agent_id: str
    capability: str
    resource: str
    expires_at_ms: int
    max_calls: int = 1
    requires_confirmation: bool = False

    def __post_init__(self) -> None:
        _require_identifier(self.grant_id, "grant_id")
        _require_identifier(self.session_id, "session_id")
        _require_identifier(self.agent_id, "agent_id")
        if not isinstance(self.capability, str) or not _CAPABILITY.fullmatch(self.capability):
            raise ValueError("capability must use a canonical lowercase identifier")
        _require_scope(self.resource, "resource")
        if type(self.expires_at_ms) is not int or self.expires_at_ms <= 0:
            raise ValueError("expires_at_ms must be a positive integer")
        if type(self.max_calls) is not int or self.max_calls <= 0:
            raise ValueError("max_calls must be a positive integer")
        if not isinstance(self.requires_confirmation, bool):
            raise ValueError("requires_confirmation must be boolean")


@dataclass(frozen=True)
class SessionBudget:
    max_actions: int
    max_output_bytes: int
    deadline_ms: int

    def __post_init__(self) -> None:
        if type(self.max_actions) is not int or self.max_actions <= 0:
            raise ValueError("max_actions must be a positive integer")
        if type(self.max_output_bytes) is not int or self.max_output_bytes < 0:
            raise ValueError("max_output_bytes must be a non-negative integer")
        if type(self.deadline_ms) is not int or self.deadline_ms <= 0:
            raise ValueError("deadline_ms must be a positive integer")


@dataclass(frozen=True)
class Approval:
    approval_id: str
    request_id: str
    session_id: str
    agent_id: str
    capability: str
    resource: str
    expires_at_ms: int

    def __post_init__(self) -> None:
        _require_identifier(self.approval_id, "approval_id")
        _require_identifier(self.request_id, "request_id")
        _require_identifier(self.session_id, "session_id")
        _require_identifier(self.agent_id, "agent_id")
        if not isinstance(self.capability, str) or not _CAPABILITY.fullmatch(self.capability):
            raise ValueError("capability must use a canonical lowercase identifier")
        _require_scope(self.resource, "resource")
        if type(self.expires_at_ms) is not int or self.expires_at_ms <= 0:
            raise ValueError("expires_at_ms must be a positive integer")


@dataclass(frozen=True)
class ToolRequest:
    request_id: str
    session_id: str
    agent_id: str
    capability: str
    resource: str
    output_limit_bytes: int = 0
    approval_id: str | None = None

    def __post_init__(self) -> None:
        _require_identifier(self.request_id, "request_id")
        _require_identifier(self.session_id, "session_id")
        _require_identifier(self.agent_id, "agent_id")
        if not isinstance(self.capability, str) or not _CAPABILITY.fullmatch(self.capability):
            raise ValueError("capability must use a canonical lowercase identifier")
        _require_scope(self.resource, "resource")
        if type(self.output_limit_bytes) is not int or self.output_limit_bytes < 0:
            raise ValueError("output_limit_bytes must be a non-negative integer")
        if self.approval_id is not None:
            _require_identifier(self.approval_id, "approval_id")


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
    request_id: str
    grant_id: str | None = None
    reserved_output_bytes: int = 0


@dataclass(frozen=True)
class AuditRecord:
    timestamp_ms: int
    request_id: str
    session_id: str
    agent_id: str
    capability: str
    resource: str
    allowed: bool
    reason: str
    grant_id: str | None
    reserved_output_bytes: int


@dataclass
class _BudgetState:
    actions_used: int = 0
    output_consumed: int = 0
    output_reserved: int = 0
    pending: dict[str, int] | None = None

    def __post_init__(self) -> None:
        if self.pending is None:
            self.pending = {}


class PolicyEngine:
    """Thread-safe policy decision core; no tool execution occurs here."""

    def __init__(
        self,
        grants: list[CapabilityGrant] | tuple[CapabilityGrant, ...],
        budgets: dict[str, SessionBudget],
        approvals: list[Approval] | tuple[Approval, ...] = (),
    ):
        self._grants: dict[str, CapabilityGrant] = {}
        grant_scopes = set()
        for grant in grants:
            if grant.grant_id in self._grants:
                raise ValueError(f"duplicate grant_id: {grant.grant_id}")
            scope = (grant.session_id, grant.agent_id, grant.capability, grant.resource)
            if scope in grant_scopes:
                raise ValueError("duplicate capability grant scope")
            grant_scopes.add(scope)
            self._grants[grant.grant_id] = grant

        self._budgets = dict(budgets)
        for session_id in self._budgets:
            _require_identifier(session_id, "budget session_id")
        self._states = {session_id: _BudgetState() for session_id in self._budgets}
        self._approvals: dict[str, Approval] = {}
        for approval in approvals:
            if approval.approval_id in self._approvals:
                raise ValueError(f"duplicate approval_id: {approval.approval_id}")
            self._approvals[approval.approval_id] = approval

        self._revoked: set[str] = set()
        self._used_approvals: set[str] = set()
        self._seen_requests: set[str] = set()
        self._grant_calls: dict[str, int] = {}
        self._audit: list[AuditRecord] = []
        self._lock = threading.RLock()

    @property
    def audit_records(self) -> tuple[AuditRecord, ...]:
        with self._lock:
            return tuple(self._audit)

    def add_approval(self, approval: Approval) -> None:
        """Register an explicit, request-bound approval supplied by a human."""
        with self._lock:
            if approval.approval_id in self._approvals:
                raise ValueError(f"duplicate approval_id: {approval.approval_id}")
            self._approvals[approval.approval_id] = approval

    def revoke(self, grant_id: str) -> bool:
        """Revoke a grant immediately; returns False for an unknown grant."""
        with self._lock:
            if grant_id not in self._grants:
                return False
            self._revoked.add(grant_id)
            return True

    def _record(
        self,
        request: ToolRequest,
        now_ms: int,
        allowed: bool,
        reason: str,
        grant_id: str | None = None,
        reserved_output_bytes: int = 0,
    ) -> PolicyDecision:
        self._audit.append(AuditRecord(
            timestamp_ms=now_ms,
            request_id=request.request_id,
            session_id=request.session_id,
            agent_id=request.agent_id,
            capability=request.capability,
            resource=request.resource,
            allowed=allowed,
            reason=reason,
            grant_id=grant_id,
            reserved_output_bytes=reserved_output_bytes,
        ))
        return PolicyDecision(
            allowed=allowed,
            reason=reason,
            request_id=request.request_id,
            grant_id=grant_id,
            reserved_output_bytes=reserved_output_bytes,
        )

    def authorize(self, request: ToolRequest, now_ms: int) -> PolicyDecision:
        """Authorize one proposed operation and reserve its output allowance.

        Request IDs are single-use, including denied requests. An allowed call
        consumes one action from both the grant and the session budget.
        """
        if type(now_ms) is not int or now_ms < 0:
            raise ValueError("now_ms must be a non-negative integer")

        with self._lock:
            if request.request_id in self._seen_requests:
                return self._record(request, now_ms, False, "duplicate_request")
            self._seen_requests.add(request.request_id)

            budget = self._budgets.get(request.session_id)
            state = self._states.get(request.session_id)
            if budget is None or state is None:
                return self._record(request, now_ms, False, "no_session_budget")
            if now_ms >= budget.deadline_ms:
                return self._record(request, now_ms, False, "session_deadline_exceeded")
            if state.actions_used >= budget.max_actions:
                return self._record(request, now_ms, False, "action_budget_exceeded")

            remaining_output = (
                budget.max_output_bytes - state.output_consumed - state.output_reserved
            )
            if request.output_limit_bytes > remaining_output:
                return self._record(request, now_ms, False, "output_budget_exceeded")

            grant = None
            for candidate in self._grants.values():
                if (
                    candidate.session_id == request.session_id
                    and candidate.agent_id == request.agent_id
                    and candidate.capability == request.capability
                    and candidate.resource == request.resource
                ):
                    grant = candidate
                    break

            if grant is None:
                return self._record(request, now_ms, False, "no_matching_grant")
            if grant.grant_id in self._revoked:
                return self._record(request, now_ms, False, "grant_revoked", grant.grant_id)
            if now_ms >= grant.expires_at_ms:
                return self._record(request, now_ms, False, "grant_expired", grant.grant_id)
            calls_used = self._grant_calls.get(grant.grant_id, 0)
            if calls_used >= grant.max_calls:
                return self._record(request, now_ms, False, "grant_call_limit_exceeded", grant.grant_id)

            approval = None
            if grant.requires_confirmation:
                if request.approval_id is None:
                    return self._record(request, now_ms, False, "confirmation_required", grant.grant_id)
                approval = self._approvals.get(request.approval_id)
                if approval is None or approval.approval_id in self._used_approvals:
                    return self._record(request, now_ms, False, "approval_invalid_or_used", grant.grant_id)
                if (
                    approval.request_id != request.request_id
                    or approval.session_id != request.session_id
                    or approval.agent_id != request.agent_id
                    or approval.capability != request.capability
                    or approval.resource != request.resource
                    or now_ms >= approval.expires_at_ms
                ):
                    return self._record(request, now_ms, False, "approval_scope_mismatch_or_expired", grant.grant_id)

            state.actions_used += 1
            state.output_reserved += request.output_limit_bytes
            state.pending[request.request_id] = request.output_limit_bytes
            self._grant_calls[grant.grant_id] = calls_used + 1
            if approval is not None:
                self._used_approvals.add(approval.approval_id)
            return self._record(
                request,
                now_ms,
                True,
                "allowed",
                grant.grant_id,
                request.output_limit_bytes,
            )

    def settle(self, request_id: str, actual_output_bytes: int, now_ms: int) -> bool:
        """Settle a completed call; over-limit output exhausts the session budget."""
        if type(actual_output_bytes) is not int or actual_output_bytes < 0:
            raise ValueError("actual_output_bytes must be a non-negative integer")
        if type(now_ms) is not int or now_ms < 0:
            raise ValueError("now_ms must be a non-negative integer")

        with self._lock:
            match = None
            for session_id, state in self._states.items():
                if request_id in state.pending:
                    match = (session_id, state)
                    break
            if match is None:
                return False

            session_id, state = match
            reserved = state.pending.pop(request_id)
            state.output_reserved -= reserved
            budget = self._budgets[session_id]
            if actual_output_bytes > reserved:
                state.output_consumed = budget.max_output_bytes
                self._audit.append(AuditRecord(
                    timestamp_ms=now_ms,
                    request_id=request_id,
                    session_id=session_id,
                    agent_id="runtime",
                    capability="runtime.output",
                    resource=session_id,
                    allowed=False,
                    reason="output_limit_exceeded",
                    grant_id=None,
                    reserved_output_bytes=reserved,
                ))
                return False

            state.output_consumed += actual_output_bytes
            self._audit.append(AuditRecord(
                timestamp_ms=now_ms,
                request_id=request_id,
                session_id=session_id,
                agent_id="runtime",
                capability="runtime.output",
                resource=session_id,
                allowed=True,
                reason="settled",
                grant_id=None,
                reserved_output_bytes=actual_output_bytes,
            ))
            return True

    def cancel(self, request_id: str, now_ms: int) -> bool:
        """Cancel a pending reservation; the attempted action remains consumed."""
        if not isinstance(now_ms, int) or now_ms < 0:
            raise ValueError("now_ms must be a non-negative integer")
        with self._lock:
            for session_id, state in self._states.items():
                if request_id in state.pending:
                    reserved = state.pending.pop(request_id)
                    state.output_reserved -= reserved
                    self._audit.append(AuditRecord(
                        timestamp_ms=now_ms,
                        request_id=request_id,
                        session_id=session_id,
                        agent_id="runtime",
                        capability="runtime.cancel",
                        resource=session_id,
                        allowed=True,
                        reason="cancelled",
                        grant_id=None,
                        reserved_output_bytes=reserved,
                    ))
                    return True
            return False

    def budget_usage(self, session_id: str) -> dict[str, int]:
        """Return a read-only snapshot of the session's current budget usage."""
        with self._lock:
            state = self._states.get(session_id)
            if state is None:
                raise KeyError(session_id)
            return {
                "actions_used": state.actions_used,
                "output_consumed": state.output_consumed,
                "output_reserved": state.output_reserved,
                "pending_calls": len(state.pending),
            }
