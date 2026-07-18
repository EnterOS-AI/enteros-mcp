#!/usr/bin/env python3
"""Ratchet the legacy monorepo away from the canonical MCP server package."""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CANONICAL_PACKAGE = "@molecule-ai/mcp-server"
RETIRED_PACKAGE = "@molecule-ai/retired-mcp-server-snapshot"
DENY_PUBLISH_SCRIPT = (
    "node -e \"console.error('Publishing this retired snapshot is disabled; "
    "use molecule-ai/molecule-mcp-server'); process.exit(1)\""
)
WORKFLOW_SUFFIXES = {".yml", ".yaml"}


def publisher_policy_violations(repo_root: Path) -> list[str]:
    """Return every way the retired server publisher is still enabled."""

    violations: list[str] = []
    package_path = repo_root / "server" / "package.json"
    package = json.loads(package_path.read_text(encoding="utf-8"))

    if package.get("name") != RETIRED_PACKAGE:
        violations.append(f"server/package.json must use retired identity {RETIRED_PACKAGE!r}")
    if package.get("private") is not True:
        violations.append("server/package.json must set private=true")
    if "publishConfig" in package:
        violations.append("server/package.json must not define publishConfig")
    if package.get("scripts", {}).get("prepublishOnly") != DENY_PUBLISH_SCRIPT:
        violations.append("server/package.json must retain the fail-closed prepublishOnly hook")

    workflow_dir = repo_root / ".gitea" / "workflows"
    for workflow_path in sorted(workflow_dir.iterdir()):
        if workflow_path.suffix not in WORKFLOW_SUFFIXES:
            continue

        workflow = workflow_path.read_text(encoding="utf-8")
        lower = workflow.lower()
        server_working_directory = re.search(
            r"working-directory\s*:\s*(?:\./)?server(?:\s|$)",
            workflow,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        server_publish_command = re.search(
            r"(?:cd\s+(?:\./)?server\b[^\n]*(?:&&|;)\s*npm\s+publish\b|"
            r"npm\s+--prefix\s+(?:\./)?server\s+publish\b)",
            workflow,
            flags=re.IGNORECASE,
        )

        if workflow_path.stem == "publish-server":
            violations.append(f"retired server publisher workflow exists: {workflow_path.name}")
        if CANONICAL_PACKAGE.lower() in lower:
            violations.append(f"canonical package referenced by workflow: {workflow_path.name}")
        if "server-v" in lower:
            violations.append(f"retired server tag trigger referenced by workflow: {workflow_path.name}")
        if re.search(r"\bnpm\s+publish\b", workflow, flags=re.IGNORECASE) and server_working_directory:
            violations.append(f"npm publish runs from server/ in workflow: {workflow_path.name}")
        if server_publish_command:
            violations.append(f"server npm publish command exists in workflow: {workflow_path.name}")

    return violations


class PublisherPolicyUnitTests(unittest.TestCase):
    def write_fixture(self, package: dict[str, object], workflows: dict[str, str]) -> Path:
        temp_dir = Path(self.enterContext(tempfile.TemporaryDirectory()))
        (temp_dir / "server").mkdir()
        (temp_dir / "server" / "package.json").write_text(
            json.dumps(package), encoding="utf-8"
        )
        workflow_dir = temp_dir / ".gitea" / "workflows"
        workflow_dir.mkdir(parents=True)
        for name, contents in workflows.items():
            (workflow_dir / name).write_text(contents, encoding="utf-8")
        return temp_dir

    def test_allows_unrelated_channel_publisher(self) -> None:
        repo_root = self.write_fixture(
            {
                "name": RETIRED_PACKAGE,
                "private": True,
                "scripts": {"prepublishOnly": DENY_PUBLISH_SCRIPT},
            },
            {
                "publish-channel.yml": """
jobs:
  publish:
    defaults:
      run:
        working-directory: channels/claude
    steps:
      - run: npm publish --access public
"""
            },
        )

        self.assertEqual([], publisher_policy_violations(repo_root))

    def test_rejects_publishable_server_package(self) -> None:
        repo_root = self.write_fixture(
            {
                "name": RETIRED_PACKAGE,
                "scripts": {"prepublishOnly": DENY_PUBLISH_SCRIPT},
                "publishConfig": {"access": "public"},
            },
            {},
        )

        violations = publisher_policy_violations(repo_root)
        self.assertIn("server/package.json must set private=true", violations)
        self.assertIn("server/package.json must not define publishConfig", violations)

    def test_rejects_server_publisher_workflow(self) -> None:
        repo_root = self.write_fixture(
            {
                "name": RETIRED_PACKAGE,
                "private": True,
                "scripts": {"prepublishOnly": DENY_PUBLISH_SCRIPT},
            },
            {
                "publish-server.yml": """
on:
  push:
    tags: ['server-v*']
jobs:
  publish:
    defaults:
      run:
        working-directory: server
    steps:
      - run: npm publish --access public
"""
            },
        )

        violations = publisher_policy_violations(repo_root)
        self.assertTrue(
            any("retired server publisher workflow exists" in item for item in violations)
        )
        self.assertTrue(
            any("retired server tag trigger referenced" in item for item in violations)
        )
        self.assertTrue(any("npm publish runs from server/" in item for item in violations))

    def test_rejects_inline_server_publish_command(self) -> None:
        repo_root = self.write_fixture(
            {
                "name": RETIRED_PACKAGE,
                "private": True,
                "scripts": {"prepublishOnly": DENY_PUBLISH_SCRIPT},
            },
            {"release.yml": "jobs:\n  release:\n    steps:\n      - run: cd server && npm publish\n"},
        )

        self.assertTrue(
            any(
                "server npm publish command exists" in item
                for item in publisher_policy_violations(repo_root)
            )
        )

    def test_rejects_canonical_package_identity_or_missing_publish_guard(self) -> None:
        repo_root = self.write_fixture(
            {"name": CANONICAL_PACKAGE, "private": True, "scripts": {}},
            {},
        )

        violations = publisher_policy_violations(repo_root)
        self.assertTrue(any("must use retired identity" in item for item in violations))
        self.assertIn(
            "server/package.json must retain the fail-closed prepublishOnly hook",
            violations,
        )


class RepositoryPublisherPolicyTest(unittest.TestCase):
    def test_legacy_repository_cannot_publish_canonical_server_package(self) -> None:
        self.assertEqual([], publisher_policy_violations(REPO_ROOT))


if __name__ == "__main__":
    unittest.main()
