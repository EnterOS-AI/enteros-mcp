"""Regression tests for sop-checklist-gate.py.

These tests import the gate script as a module so the pure logic can be
unit-tested without calling the Gitea API. Network-dependent helpers are
not exercised here.
"""

import importlib.util
import os
import sys
import unittest

# Load sop-checklist-gate.py as a module; its filename contains hyphens so
# a normal import will not work.
_GATE_SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "sop-checklist-gate.py"
)
_spec = importlib.util.spec_from_file_location("sop_checklist_gate", _GATE_SCRIPT)
assert _spec is not None and _spec.loader is not None
_gate = importlib.util.module_from_spec(_spec)
sys.modules["sop_checklist_gate"] = _gate
_spec.loader.exec_module(_gate)

render_status = _gate.render_status


class RenderStatusTestCase(unittest.TestCase):
    """Unit tests for the gate's status-rendering logic."""

    @staticmethod
    def _items(slugs):
        return [{"slug": s} for s in slugs]

    @staticmethod
    def _acks(slugs):
        return {s: {"ackers": ["peer"] if s in slugs else []} for s in slugs}

    def _body(self, slugs, filled):
        return {s: filled for s in slugs}

    def test_success_when_body_filled_and_acks_present(self):
        """Fully-acked PR with filled body checklist answers should pass."""
        slugs = ["comprehensive-testing", "local-postgres-e2e"]
        items = self._items(slugs)
        ack_state = self._acks(slugs)
        body_state = self._body(slugs, filled=True)

        state, description = render_status(items, ack_state, body_state)

        self.assertEqual(state, "success")
        self.assertIn("acked: 2/2", description)
        self.assertNotIn("body-unfilled", description)

    def test_failure_when_body_answer_missing_despite_acks(self):
        """Missing/empty PR-body checklist answers must make the gate fail,
        even when every item already has a valid peer ack.
        """
        slugs = ["comprehensive-testing", "local-postgres-e2e"]
        items = self._items(slugs)
        ack_state = self._acks(slugs)
        body_state = {slugs[0]: True, slugs[1]: False}

        state, description = render_status(items, ack_state, body_state)

        self.assertEqual(state, "failure")
        self.assertIn("body-unfilled: 1", description)
        self.assertIn("acked: 2/2", description)

    def test_failure_when_body_answer_empty_string(self):
        """A body section that is present but empty must be treated as unfilled."""
        slugs = ["comprehensive-testing"]
        items = self._items(slugs)
        ack_state = self._acks(slugs)
        body_state = {slugs[0]: False}

        state, description = render_status(items, ack_state, body_state)

        self.assertEqual(state, "failure")
        self.assertIn("body-unfilled: 1", description)

    def test_failure_when_ack_missing_despite_body_filled(self):
        """Missing acks must still fail the gate even with a filled body."""
        slugs = ["comprehensive-testing", "local-postgres-e2e"]
        items = self._items(slugs)
        ack_state = {slugs[0]: {"ackers": ["peer"]}, slugs[1]: {"ackers": []}}
        body_state = self._body(slugs, filled=True)

        state, description = render_status(items, ack_state, body_state)

        self.assertEqual(state, "failure")
        self.assertIn("missing:", description)
        self.assertNotIn("body-unfilled", description)


if __name__ == "__main__":
    unittest.main()
