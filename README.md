# molecule-mcp

Monorepo for Molecule AI's MCP (Model Context Protocol) surfaces.
Consolidated 2026-05-20 from the standalone repos
[`molecule-mcp-server`](https://git.moleculesai.app/molecule-ai/molecule-mcp-server)
and
[`molecule-mcp-claude-channel`](https://git.moleculesai.app/molecule-ai/molecule-mcp-claude-channel)
(both now archived).

## Packages

| Path | npm | Purpose |
|------|-----|---------|
| [`server/`](./server) | [`@molecule-ai/mcp-server`](https://www.npmjs.com/package/@molecule-ai/mcp-server) | MCP server exposing Molecule AI platform operations as tools for AI coding agents (workspaces, agents, files, delegations, secrets, channels, schedules). 87+ tools. Node + jest. |
| [`channels/claude/`](./channels/claude) | [`@molecule-ai/mcp-claude-channel`](https://www.npmjs.com/package/@molecule-ai/mcp-claude-channel) | Claude Code channel plugin — bridges Molecule A2A traffic into a Claude Code session. Single-file Bun runtime. |

## Layout

```
molecule-mcp/
  server/                MCP server (Node)
  channels/
    claude/              Claude Code channel plugin (Bun)
  .gitea/workflows/      monorepo CI + per-package publish workflows
```

## Why a monorepo

The server and the Claude channel ship as a coordinated pair: the channel
plugin embeds an MCP client that talks to the same protocol the server
exposes. Keeping them in one repo lets contract changes land atomically
and lets contributors see the wire shape from both ends in one diff.

## CI

Single CI workflow with path-filtered package matrix
(`.gitea/workflows/ci.yml`). Pushes that touch only `server/` run only
the server build/test; pushes that touch only `channels/claude/` run
only the Bun tests. The `all-required` sentinel job is the
branch-protection required status (pattern follows
`feedback_gitea_empty_status_check_contexts_blocks_merge`).

## Publishing

Per-package, tag-gated.

- `server-v*` → publishes `@molecule-ai/mcp-server` from `server/`
  (existing package — same npm name preserved so consumer pins keep working).
- `channel-claude-v*` → publishes `@molecule-ai/mcp-claude-channel`
  from `channels/claude/` (new package).

Both workflows require the `NPM_TOKEN` secret. Set `publishConfig.access`
to `"public"` in each `package.json` (already done).

## Contributing

PRs target `main`. Two non-author APPROVEs are required before merge
(per house standard) — no admin-bypass, no CI skip. Use a scoped persona
token for the merge (whitelist persona configured in branch protection),
not a founder PAT.

Source-side history for both former repos is preserved via subtree
merge — `git log --follow server/<file>` and `git log --follow
channels/claude/<file>` show pre-monorepo commits.
