# molecule-mcp

Monorepo for Molecule AI's MCP (Model Context Protocol) surfaces.
Consolidated 2026-05-20 from the standalone repos
[`molecule-mcp-server`](https://git.moleculesai.app/molecule-ai/molecule-mcp-server)
and
[`molecule-mcp-claude-channel`](https://git.moleculesai.app/molecule-ai/molecule-mcp-claude-channel)
(both active again).

> **Superseded:** both standalone repositories are the canonical source, CI,
> and release locations. The imported package trees below remain buildable for
> historical verification, but their package identities and publish lifecycles
> are retired and CI ratchets both old publishers off.

## Packages

| Path | npm | Purpose |
|------|-----|---------|
| [`server/`](./server) | Formerly `@molecule-ai/mcp-server` | Retired snapshot; use the active standalone repository for source, releases, and the internal Gitea npm package. |
| [`channels/claude/`](./channels/claude) | Formerly `@molecule-ai/mcp-claude-channel` | Retired snapshot; use the active standalone Gitea marketplace repository for installs and tagged releases. |

## Layout

```
molecule-mcp/
  server/                MCP server (Node)
  channels/
    claude/              Claude Code channel plugin (Bun)
  .gitea/workflows/      historical build/test CI + publisher ratchet
```

## Historical monorepo rationale

This consolidation was intended to coordinate server and channel contract
changes. Source and release ownership later moved back to the standalone
repositories; this snapshot remains only for historical verification.

## CI

Single CI workflow with path-filtered package matrix
(`.gitea/workflows/ci.yml`). Pushes that touch only `server/` run only
the server build/test; pushes that touch only `channels/claude/` run
only the Bun tests. An always-on publisher-retirement test rejects any attempt
to make either package publishable, repoint its manifest here, or restore either
release workflow. The
`all-required` sentinel job is the
branch-protection required status (pattern follows
`feedback_gitea_empty_status_check_contexts_blocks_merge`).

## Publishing

The server publisher lives in the standalone
[`molecule-mcp-server`](https://git.moleculesai.app/molecule-ai/molecule-mcp-server)
repository, which publishes `@molecule-ai/mcp-server` to the internal Gitea npm
registry. Do not create `server-v*` tags or publish `server/` from this repo.

The Claude channel distributes directly through the standalone
[`molecule-mcp-claude-channel`](https://git.moleculesai.app/molecule-ai/molecule-mcp-claude-channel)
Gitea marketplace and its `v*` tags. Do not create `channel-claude-v*` tags or
publish `channels/claude/` from this repo.

## Contributing

PRs target `main`. Two non-author APPROVEs are required before merge
(per house standard) — no admin-bypass, no CI skip. Use a scoped persona
token for the merge (whitelist persona configured in branch protection),
not a founder PAT.

Open product and release changes against the corresponding standalone
repository, not this snapshot.

Source-side history imported from both standalone repos is preserved via subtree
merge — `git log --follow server/<file>` and `git log --follow
channels/claude/<file>` show pre-monorepo commits.
