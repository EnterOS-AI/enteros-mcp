#!/usr/bin/env python3
"""Ratchet the legacy monorepo away from both standalone package owners."""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_SUFFIXES = {".yml", ".yaml"}
PUBLISH_COMMAND = r"(?:npm|pnpm|bun)\s+publish\b"
PACKAGE_POLICIES = (
    {
        "path": "server",
        "legacy_name": "@molecule-ai/mcp-server",
        "retired_name": "@molecule-ai/retired-mcp-server-snapshot",
        "repository": "https://git.moleculesai.app/molecule-ai/molecule-mcp-server.git",
        "workflow_stem": "publish-server",
        "tag_prefix": "server-v",
        "deny_publish": (
            "node -e \"console.error('Publishing this retired snapshot is disabled; "
            "use molecule-ai/molecule-mcp-server'); process.exit(1)\""
        ),
    },
    {
        "path": "channels/claude",
        "legacy_name": "@molecule-ai/mcp-claude-channel",
        "retired_name": "@molecule-ai/retired-mcp-claude-channel-snapshot",
        "repository": (
            "https://git.moleculesai.app/molecule-ai/"
            "molecule-mcp-claude-channel.git"
        ),
        "workflow_stem": "publish-channel-claude",
        "tag_prefix": "channel-claude-v",
        "deny_publish": (
            "node -e \"console.error('Publishing this retired snapshot is disabled; "
            "use molecule-ai/molecule-mcp-claude-channel'); process.exit(1)\""
        ),
    },
)


def valid_package(policy: dict[str, str]) -> dict[str, object]:
    return {
        "name": policy["retired_name"],
        "private": True,
        "scripts": {"prepublishOnly": policy["deny_publish"]},
        "repository": {"type": "git", "url": policy["repository"]},
    }


def publisher_policy_violations(repo_root: Path) -> list[str]:
    """Return every way either retired package publisher is still enabled."""

    violations: list[str] = []
    for policy in PACKAGE_POLICIES:
        package_path = repo_root / policy["path"] / "package.json"
        package = json.loads(package_path.read_text(encoding="utf-8"))
        label = f"{policy['path']}/package.json"

        if package.get("name") != policy["retired_name"]:
            violations.append(f"{label} must use retired identity {policy['retired_name']!r}")
        if package.get("private") is not True:
            violations.append(f"{label} must set private=true")
        if "publishConfig" in package:
            violations.append(f"{label} must not define publishConfig")
        if package.get("scripts", {}).get("prepublishOnly") != policy["deny_publish"]:
            violations.append(f"{label} must retain the fail-closed prepublishOnly hook")
        repository = package.get("repository")
        if not isinstance(repository, dict) or repository.get("url") != policy["repository"]:
            violations.append(f"{label} must point to {policy['repository']}")
        if isinstance(repository, dict) and "directory" in repository:
            violations.append(f"{label} must not point into the retired monorepo")

    workflow_dir = repo_root / ".gitea" / "workflows"
    for workflow_path in sorted(workflow_dir.iterdir()):
        if workflow_path.suffix not in WORKFLOW_SUFFIXES:
            continue

        workflow = workflow_path.read_text(encoding="utf-8")
        lower = workflow.lower()
        for policy in PACKAGE_POLICIES:
            package_path = re.escape(policy["path"])
            working_directory = re.search(
                rf"working-directory\s*:\s*(?:\./)?{package_path}(?:\s|$)",
                workflow,
                flags=re.IGNORECASE | re.MULTILINE,
            )
            direct_publish = re.search(
                rf"(?:cd\s+(?:\./)?{package_path}\b[^\n]*(?:&&|;)\s*"
                rf"{PUBLISH_COMMAND}|(?:npm|pnpm|bun)\s+--prefix\s+"
                rf"(?:\./)?{package_path}\s+publish\b)",
                workflow,
                flags=re.IGNORECASE,
            )

            if workflow_path.stem == policy["workflow_stem"]:
                violations.append(f"retired publisher workflow exists: {workflow_path.name}")
            if policy["legacy_name"].lower() in lower:
                violations.append(f"legacy package referenced by workflow: {workflow_path.name}")
            if policy["tag_prefix"] in lower:
                violations.append(f"retired tag trigger referenced by workflow: {workflow_path.name}")
            if re.search(PUBLISH_COMMAND, workflow, flags=re.IGNORECASE) and working_directory:
                violations.append(
                    f"package publish runs from {policy['path']}/ in workflow: "
                    f"{workflow_path.name}"
                )
            if direct_publish:
                violations.append(
                    f"package publish command targets {policy['path']}/ in workflow: "
                    f"{workflow_path.name}"
                )

    return violations


class PublisherPolicyUnitTests(unittest.TestCase):
    def write_fixture(
        self,
        packages: dict[str, dict[str, object]] | None = None,
        workflows: dict[str, str] | None = None,
    ) -> Path:
        temp_dir = Path(self.enterContext(tempfile.TemporaryDirectory()))
        for policy in PACKAGE_POLICIES:
            package_path = temp_dir / policy["path"] / "package.json"
            package_path.parent.mkdir(parents=True)
            package = (packages or {}).get(policy["path"], valid_package(policy))
            package_path.write_text(json.dumps(package), encoding="utf-8")
        workflow_dir = temp_dir / ".gitea" / "workflows"
        workflow_dir.mkdir(parents=True)
        for name, contents in (workflows or {}).items():
            (workflow_dir / name).write_text(contents, encoding="utf-8")
        return temp_dir

    def test_allows_unrelated_package_publisher(self) -> None:
        repo_root = self.write_fixture(
            workflows={
                "publish-other.yml": """
jobs:
  publish:
    defaults:
      run:
        working-directory: tools/other
    steps:
      - run: npm publish
"""
            }
        )

        self.assertEqual([], publisher_policy_violations(repo_root))

    def test_rejects_publishable_or_misdirected_package_manifests(self) -> None:
        for policy in PACKAGE_POLICIES:
            with self.subTest(path=policy["path"]):
                repo_root = self.write_fixture(
                    packages={
                        policy["path"]: {
                            "name": policy["legacy_name"],
                            "scripts": {},
                            "publishConfig": {"access": "public"},
                            "repository": {
                                "url": "https://git.moleculesai.app/molecule-ai/molecule-mcp.git",
                                "directory": policy["path"],
                            },
                        }
                    }
                )

                violations = publisher_policy_violations(repo_root)
                self.assertTrue(any("must use retired identity" in item for item in violations))
                self.assertTrue(any("must set private=true" in item for item in violations))
                self.assertTrue(any("must not define publishConfig" in item for item in violations))
                self.assertTrue(any("fail-closed prepublishOnly" in item for item in violations))
                self.assertTrue(any("must point to" in item for item in violations))
                self.assertTrue(any("must not point into" in item for item in violations))

    def test_rejects_each_retired_publisher_workflow(self) -> None:
        for policy in PACKAGE_POLICIES:
            with self.subTest(path=policy["path"]):
                repo_root = self.write_fixture(
                    workflows={
                        f"{policy['workflow_stem']}.yml": f"""
on:
  push:
    tags: ['{policy['tag_prefix']}*']
jobs:
  publish:
    defaults:
      run:
        working-directory: {policy['path']}
    steps:
      - name: Publish {policy['legacy_name']}
        run: npm publish
"""
                    }
                )

                violations = publisher_policy_violations(repo_root)
                self.assertTrue(any("retired publisher workflow exists" in item for item in violations))
                self.assertTrue(any("legacy package referenced" in item for item in violations))
                self.assertTrue(any("retired tag trigger referenced" in item for item in violations))
                self.assertTrue(any("package publish runs from" in item for item in violations))

    def test_rejects_direct_publish_commands_for_each_package(self) -> None:
        for policy in PACKAGE_POLICIES:
            with self.subTest(path=policy["path"]):
                repo_root = self.write_fixture(
                    workflows={
                        "release.yml": (
                            "jobs:\n  release:\n    steps:\n"
                            f"      - run: cd {policy['path']} && bun publish\n"
                        )
                    }
                )

                self.assertTrue(
                    any(
                        "package publish command targets" in item
                        for item in publisher_policy_violations(repo_root)
                    )
                )


class RepositoryPublisherPolicyTest(unittest.TestCase):
    def test_legacy_repository_cannot_publish_standalone_owned_packages(self) -> None:
        self.assertEqual([], publisher_policy_violations(REPO_ROOT))

    def test_retirement_runbook_names_the_external_historical_tag_kill_switch(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        for required in (
            "pre-retirement commit",
            "server-v*",
            "channel-claude-v*",
            "NPM_TOKEN",
            "Gitea Actions is disabled",
            "repository archived",
        ):
            with self.subTest(required=required):
                self.assertIn(required, readme)


if __name__ == "__main__":
    unittest.main()
