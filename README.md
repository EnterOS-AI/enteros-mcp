# molecule-mcp

Monorepo for Molecule AI's MCP (Model Context Protocol) surfaces.
Consolidated 2026-05-20 from the standalone repos
[`molecule-mcp-server`](https://git.moleculesai.app/molecule-ai/molecule-mcp-server)
and
[`molecule-mcp-claude-channel`](https://git.moleculesai.app/molecule-ai/molecule-mcp-claude-channel)
(both active again).

> **Server publisher retired here:** the standalone
> [`molecule-mcp-server`](https://git.moleculesai.app/molecule-ai/molecule-mcp-server)
> repository is the only source and publisher for `@molecule-ai/mcp-server`.
> The `server/` tree below is retained as a historical snapshot and cannot be
> published: its package uses a retired name, is private, rejects the publish
> lifecycle, and CI ratchets the old publisher off.

## Packages

| Path | npm | Purpose |
|------|-----|---------|
| [`server/`](./server) | Formerly `@molecule-ai/mcp-server` | Retired snapshot; use the active standalone repository for source, releases, and the internal Gitea npm package. |
| [`channels/claude/`](./channels/claude) | [`@molecule-ai/mcp-claude-channel`](https://www.npmjs.com/package/@molecule-ai/mcp-claude-channel) | Claude Code channel plugin — bridges Molecule A2A traffic into a Claude Code session. Single-file Bun runtime. |

## Layout

```
molecule-mcp/
  server/                MCP server (Node)
  channels/
    claude/              Claude Code channel plugin (Bun)
  .gitea/workflows/      monorepo CI + Claude-channel publish workflow
```

## Historical monorepo rationale

This consolidation was intended to coordinate server and channel contract
changes. The server's source and package ownership later moved back to the
standalone repository; this snapshot remains only for historical verification.

## CI

Single CI workflow with path-filtered package matrix
(`.gitea/workflows/ci.yml`). Pushes that touch only `server/` run only
the server build/test; pushes that touch only `channels/claude/` run
only the Bun tests. An always-on publisher-retirement test rejects any attempt
to make `server/` publishable or restore a server release workflow. The
`all-required` sentinel job is the
branch-protection required status (pattern follows
`feedback_gitea_empty_status_check_contexts_blocks_merge`).

## Publishing

The server publisher has moved to the standalone
[`molecule-mcp-server`](https://git.moleculesai.app/molecule-ai/molecule-mcp-server)
repository, which publishes `@molecule-ai/mcp-server` to the internal Gitea npm
registry. Do not create `server-v*` tags or publish `server/` from this repo.

- `channel-claude-v*` → publishes `@molecule-ai/mcp-claude-channel`
  from `channels/claude/`.

The Claude channel publisher is unrelated to the retired server package and is
unchanged by this ownership cutover.

## Contributing

PRs target `main`. Two non-author APPROVEs are required before merge
(per house standard) — no admin-bypass, no CI skip. Use a scoped persona
token for the merge (whitelist persona configured in branch protection),
not a founder PAT.

Open MCP server product and release changes against the standalone
`molecule-mcp-server` repository, not this snapshot.

Source-side history imported from both standalone repos is preserved via subtree
merge — `git log --follow server/<file>` and `git log --follow
channels/claude/<file>` show pre-monorepo commits.
