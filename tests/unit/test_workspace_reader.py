import os
import tempfile
import unittest

from runtime.agent_policy import CapabilityGrant, PolicyEngine, SessionBudget
from runtime.workspace_reader import WorkspaceReadExecutor


class WorkspaceReadExecutorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.temp.name, "workspace")
        os.mkdir(self.root)
        os.mkdir(os.path.join(self.root, "docs"))
        with open(os.path.join(self.root, "README.md"), "wb") as stream:
            stream.write(b"AgentSON workspace read test\n")
        with open(os.path.join(self.root, "docs", "guide.md"), "wb") as stream:
            stream.write(b"nested guide\n")
        self.grant = CapabilityGrant(
            grant_id="read-readme",
            session_id="session-1",
            agent_id="agent-1",
            capability="workspace.read",
            resource="workspace:/README.md",
            expires_at_ms=2_000,
            max_calls=10,
        )
        self.budget = SessionBudget(
            max_actions=10,
            max_output_bytes=2_000,
            deadline_ms=1_500,
        )
        self.policy = PolicyEngine([self.grant], {"session-1": self.budget})
        self.executor = WorkspaceReadExecutor(self.policy, self.root)

    def tearDown(self):
        self.temp.cleanup()

    def read(self, request_id="read-1", **overrides):
        values = {
            "request_id": request_id,
            "session_id": "session-1",
            "agent_id": "agent-1",
            "relative_path": "README.md",
            "output_limit_bytes": 100,
            "now_ms": 100,
        }
        values.update(overrides)
        return self.executor.read_file(**values)

    def test_authorized_read_returns_bytes_and_settles_budget(self):
        result = self.read()
        self.assertTrue(result.allowed)
        self.assertEqual(result.content, b"AgentSON workspace read test\n")
        self.assertEqual(result.resource, "workspace:/README.md")
        usage = self.policy.budget_usage("session-1")
        self.assertEqual(usage["output_consumed"], len(result.content))
        self.assertEqual(usage["output_reserved"], 0)

    def test_missing_grant_denies_before_open(self):
        policy = PolicyEngine([], {"session-1": self.budget})
        executor = WorkspaceReadExecutor(policy, self.root)
        result = executor.read_file(
            request_id="denied",
            session_id="session-1",
            agent_id="agent-1",
            relative_path="README.md",
            output_limit_bytes=100,
            now_ms=100,
        )
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "no_matching_grant")
        self.assertEqual(policy.budget_usage("session-1")["actions_used"], 0)

    def test_grant_is_bound_to_exact_file_resource(self):
        result = self.read(relative_path="docs/guide.md")
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "no_matching_grant")

    def test_parent_traversal_rejected_before_authorization(self):
        result = self.read(relative_path="../outside.txt")
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "invalid_request_or_resource_path")
        self.assertEqual(self.policy.audit_records, ())

    def test_absolute_path_rejected(self):
        result = self.read(relative_path="/etc/passwd")
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "invalid_request_or_resource_path")

    def test_backslash_path_rejected(self):
        result = self.read(relative_path="..\\outside.txt")
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "invalid_request_or_resource_path")

    def test_final_symlink_is_not_followed(self):
        outside = os.path.join(self.temp.name, "outside.txt")
        with open(outside, "wb") as stream:
            stream.write(b"secret")
        link = os.path.join(self.root, "link.txt")
        os.symlink(outside, link)
        grant = CapabilityGrant(
            grant_id="read-link",
            session_id="session-1",
            agent_id="agent-1",
            capability="workspace.read",
            resource="workspace:/link.txt",
            expires_at_ms=2_000,
        )
        policy = PolicyEngine([grant], {"session-1": self.budget})
        executor = WorkspaceReadExecutor(policy, self.root)
        result = executor.read_file(
            request_id="link",
            session_id="session-1",
            agent_id="agent-1",
            relative_path="link.txt",
            output_limit_bytes=100,
            now_ms=100,
        )
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "resource_unavailable")
        self.assertIsNone(result.content)

    def test_intermediate_symlink_is_not_followed(self):
        outside = os.path.join(self.temp.name, "outside-dir")
        os.mkdir(outside)
        with open(os.path.join(outside, "secret.txt"), "wb") as stream:
            stream.write(b"secret")
        os.symlink(outside, os.path.join(self.root, "linked-dir"))
        grant = CapabilityGrant(
            grant_id="read-linked",
            session_id="session-1",
            agent_id="agent-1",
            capability="workspace.read",
            resource="workspace:/linked-dir/secret.txt",
            expires_at_ms=2_000,
        )
        policy = PolicyEngine([grant], {"session-1": self.budget})
        executor = WorkspaceReadExecutor(policy, self.root)
        result = executor.read_file(
            request_id="linked",
            session_id="session-1",
            agent_id="agent-1",
            relative_path="linked-dir/secret.txt",
            output_limit_bytes=100,
            now_ms=100,
        )
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "resource_unavailable")

    def test_directory_is_not_read_as_a_file(self):
        grant = CapabilityGrant(
            grant_id="read-dir",
            session_id="session-1",
            agent_id="agent-1",
            capability="workspace.read",
            resource="workspace:/docs",
            expires_at_ms=2_000,
        )
        policy = PolicyEngine([grant], {"session-1": self.budget})
        executor = WorkspaceReadExecutor(policy, self.root)
        result = executor.read_file(
            request_id="directory",
            session_id="session-1",
            agent_id="agent-1",
            relative_path="docs",
            output_limit_bytes=100,
            now_ms=100,
        )
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "not_regular_file")

    def test_output_limit_is_enforced_and_reservation_cancelled(self):
        result = self.read(output_limit_bytes=4)
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "output_limit_exceeded")
        usage = self.policy.budget_usage("session-1")
        self.assertEqual(usage["output_reserved"], 0)
        self.assertEqual(usage["actions_used"], 1)

    def test_empty_file_can_be_read_with_zero_output_budget(self):
        with open(os.path.join(self.root, "empty.txt"), "wb"):
            pass
        grant = CapabilityGrant(
            grant_id="read-empty",
            session_id="session-1",
            agent_id="agent-1",
            capability="workspace.read",
            resource="workspace:/empty.txt",
            expires_at_ms=2_000,
        )
        policy = PolicyEngine([grant], {"session-1": self.budget})
        executor = WorkspaceReadExecutor(policy, self.root)
        result = executor.read_file(
            request_id="empty",
            session_id="session-1",
            agent_id="agent-1",
            relative_path="empty.txt",
            output_limit_bytes=0,
            now_ms=100,
        )
        self.assertTrue(result.allowed)
        self.assertEqual(result.content, b"")

    def test_symlink_workspace_root_is_rejected(self):
        linked_root = os.path.join(self.temp.name, "workspace-link")
        os.symlink(self.root, linked_root)
        executor = WorkspaceReadExecutor(self.policy, linked_root)
        result = executor.read_file(
            request_id="root-link",
            session_id="session-1",
            agent_id="agent-1",
            relative_path="README.md",
            output_limit_bytes=100,
            now_ms=100,
        )
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "resource_unavailable")

    def test_invalid_completion_time_does_not_reserve_budget(self):
        result = self.read(completed_at_ms=99)
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "invalid_request_or_resource_path")
        self.assertEqual(self.policy.budget_usage("session-1")["actions_used"], 0)

    def test_per_read_hard_limit_rejected_before_authorization(self):
        result = self.read(output_limit_bytes=8 * 1024 * 1024 + 1)
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "invalid_request_or_resource_path")
        self.assertEqual(self.policy.budget_usage("session-1")["actions_used"], 0)

    def test_non_absolute_workspace_root_rejected(self):
        with self.assertRaisesRegex(ValueError, "absolute"):
            WorkspaceReadExecutor(self.policy, ".")

    def test_nested_regular_file_read_with_exact_grant(self):
        grant = CapabilityGrant(
            grant_id="read-guide",
            session_id="session-1",
            agent_id="agent-1",
            capability="workspace.read",
            resource="workspace:/docs/guide.md",
            expires_at_ms=2_000,
        )
        policy = PolicyEngine([grant], {"session-1": self.budget})
        executor = WorkspaceReadExecutor(policy, self.root)
        result = executor.read_file(
            request_id="guide",
            session_id="session-1",
            agent_id="agent-1",
            relative_path="docs/guide.md",
            output_limit_bytes=100,
            now_ms=100,
        )
        self.assertTrue(result.allowed)
        self.assertEqual(result.content, b"nested guide\n")


if __name__ == "__main__":
    unittest.main()
