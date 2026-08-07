# Note — filesystem MCP vs built-in file tools

You likely do **not** need a filesystem MCP server. Claude Code already ships built-in
`Read`/`Write`/`Edit`/`Glob`/`Grep` tools scoped to your working directory — that already
covers most "let it touch files" use cases without adding another server, another
process, and another set of scopes to reason about.

## When a filesystem MCP *would* add value

- You need access **outside** the current project's working directory (e.g. a shared
  drive, a second repo checked out elsewhere) and want that scoped explicitly rather
  than just `cd`-ing there.
- You want a **read-only** mount of a directory for reference (e.g. a docs repo) with
  no risk of accidental writes, enforced by the MCP server's own config rather than by
  hoping the model behaves.
- You're integrating a non-Claude-Code tool that speaks MCP and needs the same
  filesystem access surface.

## If you do add one

- Scope it to the narrowest directory that satisfies the need — not your entire `$HOME`.
- Prefer read-only mode unless a write is genuinely required.
- Treat it the same as any other MCP server for the tool-sprawl question in the main
  README: does this earn a permanent slot, or would `cd` and the built-in tools do?
