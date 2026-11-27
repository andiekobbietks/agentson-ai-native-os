from concurrent.futures import ThreadPoolExecutor
import unittest

from runtime.agent_policy import (
    Approval,
    CapabilityGrant,
    PolicyEngine,
    SessionBudget,
    ToolRequest,
)


class AgentPolicyTests(unittest.TestCase):
    def setUp(self):
        self.grant = CapabilityGrant(
            grant_id="grant-1",
            session_id="session-1",
            agent_id="agent-1",
            capability="workspace.read",
            resource="workspace:/repo",
            expires_at_ms=2_000,
            max_calls=10,
        )
        self.budget = SessionBudget(
            max_actions=10,
            max_output_bytes=1_000,
            deadline_ms=1_500,
        )
        self.engine = PolicyEngine(
            grants=[self.grant],
            budgets={"session-1": self.budget},
        )

    def request(self, request_id="req-1", **overrides):
        values = {
            "request_id": request_id,
            "session_id": "session-1",
            "agent_id": "agent-1",
            "capability": "workspace.read",
            "resource": "workspace:/repo",
            "output_limit_bytes": 100,
        }
        values.update(overrides)
        return ToolRequest(**values)

    def test_deny_by_default_without_grant(self):
        engine = PolicyEngine([], {"session-1": self.budget})
        decision = engine.authorize(self.request(), now_ms=100)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "no_matching_grant")

    def test_exact_grant_allows_and_audits(self):
        decision = self.engine.authorize(self.request(), now_ms=100)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.reason, "allowed")
        self.assertEqual(decision.grant_id, "grant-1")
        self.assertEqual(self.engine.audit_records[-1].reason, "allowed")

    def test_resource_scope_is_exact(self):
        decision = self.engine.authorize(
            self.request(resource="workspace:/other"),
            now_ms=100,
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "no_matching_grant")

    def test_session_and_agent_are_bound(self):
        wrong_session = self.engine.authorize(
            self.request(session_id="session-2"),
            now_ms=100,
        )
        wrong_agent = self.engine.authorize(
            self.request(request_id="req-2", agent_id="agent-2"),
            now_ms=100,
        )
        self.assertEqual(wrong_session.reason, "no_session_budget")
        self.assertEqual(wrong_agent.reason, "no_matching_grant")

    def test_expired_grant_denied(self):
        decision = self.engine.authorize(self.request(), now_ms=2_000)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "grant_expired")

    def test_revoked_grant_denied(self):
        self.assertTrue(self.engine.revoke("grant-1"))
        decision = self.engine.authorize(self.request(), now_ms=100)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "grant_revoked")
        self.assertFalse(self.engine.revoke("missing"))

    def test_grant_call_limit_enforced(self):
        grant = CapabilityGrant(
            grant_id="one-shot",
            session_id="session-1",
            agent_id="agent-1",
            capability="workspace.read",
            resource="workspace:/repo",
            expires_at_ms=2_000,
            max_calls=1,
        )
        engine = PolicyEngine([grant], {"session-1": self.budget})
        self.assertTrue(engine.authorize(self.request(), 100).allowed)
        second = engine.authorize(self.request("req-2"), 101)
        self.assertEqual(second.reason, "grant_call_limit_exceeded")

    def test_session_action_budget_enforced(self):
        budget = SessionBudget(max_actions=1, max_output_bytes=1_000, deadline_ms=1_500)
        engine = PolicyEngine([self.grant], {"session-1": budget})
        self.assertTrue(engine.authorize(self.request(), 100).allowed)
        second = engine.authorize(self.request("req-2"), 101)
        self.assertEqual(second.reason, "action_budget_exceeded")

    def test_output_reservation_and_refund(self):
        first = self.engine.authorize(self.request(output_limit_bytes=600), 100)
        self.assertTrue(first.allowed)
        self.assertEqual(self.engine.budget_usage("session-1")["output_reserved"], 600)
        self.assertTrue(self.engine.settle("req-1", actual_output_bytes=200, now_ms=110))
        usage = self.engine.budget_usage("session-1")
        self.assertEqual(usage["output_consumed"], 200)
        self.assertEqual(usage["output_reserved"], 0)
        second = self.engine.authorize(
            self.request("req-2", output_limit_bytes=800),
            120,
        )
        self.assertTrue(second.allowed)

    def test_output_overrun_exhausts_budget(self):
        self.assertTrue(self.engine.authorize(self.request(output_limit_bytes=100), 100).allowed)
        self.assertFalse(self.engine.settle("req-1", actual_output_bytes=101, now_ms=110))
        next_decision = self.engine.authorize(
            self.request("req-2", output_limit_bytes=1),
            120,
        )
        self.assertEqual(next_decision.reason, "output_budget_exceeded")

    def test_session_deadline_enforced(self):
        decision = self.engine.authorize(self.request(), now_ms=1_500)
        self.assertEqual(decision.reason, "session_deadline_exceeded")

    def test_confirmation_is_request_bound_and_single_use(self):
        grant = CapabilityGrant(
            grant_id="grant-sensitive",
            session_id="session-1",
            agent_id="agent-1",
            capability="workspace.write",
            resource="workspace:/repo/config.json",
            expires_at_ms=2_000,
            max_calls=2,
            requires_confirmation=True,
        )
        engine = PolicyEngine(
            [grant],
            {"session-1": self.budget},
        )
        request = self.request(
            "write-1",
            capability="workspace.write",
            resource="workspace:/repo/config.json",
            output_limit_bytes=0,
        )
        self.assertEqual(engine.authorize(request, 100).reason, "confirmation_required")
        approval = Approval(
            approval_id="approval-1",
            request_id="write-2",
            session_id="session-1",
            agent_id="agent-1",
            capability="workspace.write",
            resource="workspace:/repo/config.json",
            expires_at_ms=500,
        )
        engine.add_approval(approval)
        approved_request = self.request(
            "write-2",
            capability="workspace.write",
            resource="workspace:/repo/config.json",
            output_limit_bytes=0,
            approval_id="approval-1",
        )
        self.assertTrue(engine.authorize(approved_request, 200).allowed)
        replay = self.request(
            "write-3",
            capability="workspace.write",
            resource="workspace:/repo/config.json",
            output_limit_bytes=0,
            approval_id="approval-1",
        )
        self.assertEqual(engine.authorize(replay, 201).reason, "approval_invalid_or_used")

    def test_approval_scope_mismatch_denied(self):
        grant = CapabilityGrant(
            grant_id="grant-sensitive",
            session_id="session-1",
            agent_id="agent-1",
            capability="workspace.write",
            resource="workspace:/repo/config.json",
            expires_at_ms=2_000,
            requires_confirmation=True,
        )
        approval = Approval(
            approval_id="approval-1",
            request_id="req-other",
            session_id="session-1",
            agent_id="agent-1",
            capability="workspace.write",
            resource="workspace:/repo/config.json",
            expires_at_ms=500,
        )
        engine = PolicyEngine([grant], {"session-1": self.budget}, [approval])
        request = self.request(
            "req-1",
            capability="workspace.write",
            resource="workspace:/repo/config.json",
            approval_id="approval-1",
        )
        self.assertEqual(
            engine.authorize(request, 200).reason,
            "approval_scope_mismatch_or_expired",
        )

    def test_request_ids_are_single_use_even_after_denial(self):
        first = self.engine.authorize(
            self.request(resource="workspace:/missing"),
            now_ms=100,
        )
        replay = self.engine.authorize(self.request(), now_ms=101)
        self.assertEqual(first.reason, "no_matching_grant")
        self.assertEqual(replay.reason, "duplicate_request")

    def test_cancel_releases_output_reservation_but_not_action(self):
        self.assertTrue(self.engine.authorize(self.request(), 100).allowed)
        self.assertTrue(self.engine.cancel("req-1", now_ms=110))
        usage = self.engine.budget_usage("session-1")
        self.assertEqual(usage["output_reserved"], 0)
        self.assertEqual(usage["actions_used"], 1)
        self.assertFalse(self.engine.cancel("req-1", now_ms=111))

    def test_wildcard_scopes_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "exact"):
            CapabilityGrant(
                grant_id="wild",
                session_id="session-1",
                agent_id="agent-1",
                capability="workspace.read",
                resource="workspace:*",
                expires_at_ms=2_000,
            )

    def test_concurrent_requests_cannot_exceed_action_budget(self):
        budget = SessionBudget(max_actions=5, max_output_bytes=0, deadline_ms=1_500)
        grant = CapabilityGrant(
            grant_id="parallel",
            session_id="session-1",
            agent_id="agent-1",
            capability="workspace.read",
            resource="workspace:/repo",
            expires_at_ms=2_000,
            max_calls=20,
        )
        engine = PolicyEngine([grant], {"session-1": budget})

        def authorize(index):
            request = self.request(f"parallel-{index}", output_limit_bytes=0)
            return engine.authorize(request, now_ms=100).allowed

        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(authorize, range(20)))
        self.assertEqual(sum(results), 5)
        self.assertEqual(engine.budget_usage("session-1")["actions_used"], 5)

    def test_duplicate_grant_scope_rejected(self):
        second = CapabilityGrant(
            grant_id="grant-2",
            session_id="session-1",
            agent_id="agent-1",
            capability="workspace.read",
            resource="workspace:/repo",
            expires_at_ms=3_000,
        )
        with self.assertRaisesRegex(ValueError, "duplicate capability grant scope"):
            PolicyEngine([self.grant, second], {"session-1": self.budget})

    def test_duplicate_grant_ids_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate grant_id"):
            PolicyEngine([self.grant, self.grant], {"session-1": self.budget})


if __name__ == "__main__":
    unittest.main()
