# 05 — MCP (Model Context Protocol)

## At a glance

| | |
| --- | --- |
| **Level** | Intermediate+ |
| **Time** | ~1 h |
| **Prereq** | [04 — Subagents](../04-subagents/) |
| **Artifacts** | [`lessons/artifacts/mcp/`](../artifacts/mcp/) |

## Why this matters

You're on-call. A page fires. You want Claude to check the actual open PRs, the actual
CI run status, and the actual incident ticket — not paste them in yourself, one tab at a
time, mid-incident. Copy-pasting API responses into chat during an incident is slow and
error-prone exactly when you can least afford either. **MCP** lets Claude call real
tools against real systems (GitHub, your issue tracker, your observability stack)
directly, with scoped credentials — instead of you being the human API client.

## Concept primer

**MCP (Model Context Protocol)** is a standard way for an AI client (Claude Code) to
talk to a **server** that exposes **tools** (callable actions) and **resources**
(readable data) from some external system.

| Term | Meaning |
| --- | --- |
| **MCP server** | A process that speaks MCP and wraps one system (GitHub, a DB, a ticket tracker) |
| **Tool** | A callable action the server exposes (e.g. `create_pr_comment`) |
| **Resource** | Readable data the server exposes (e.g. a file, a ticket) — often thinner than tools |
| **Scope** | What the server's credentials are allowed to do (read-only vs write, which repos/orgs) |
| **Auth** | How the server authenticates to the external system — usually a token in env, never inline in config |

- **Tools over resources, in practice**: many MCP servers' resources are empty or
  minimal — the useful surface is almost always the tools. Don't conclude a server is
  "down" just because its resource list is empty.
- **Scope tightly**: a GitHub MCP server with a token that can push to any repo in your
  org is a bigger blast radius than one scoped to a single repo, read-only where
  possible.
- **Tool sprawl is a real cost**: every MCP server you add is more tool definitions in
  context on every turn, more surface for the model to pick the wrong tool, and another
  credential to rotate and audit. Add servers because a workflow needs them, not because
  they exist.

```text
Claude Code  <--MCP-->  github-mcp-server  <--API-->  GitHub
             <--MCP-->  jira-mcp-server    <--API-->  Jira
```

> **Token note:** MCP tool *definitions* (names + schemas) load into context for every
> connected server, every turn — this is a real, ongoing budget cost, separate from
> whatever tokens a coaching skill like `/self-assessment` would use. More servers
> connected ≠ free.

## Hands-on walkthrough

1. **Inventory what you'd actually reach for.**
   - Action: name one system you check manually during a PR review or on-call rotation
     right now (GitHub, Jira/Linear, a metrics dashboard, PagerDuty).
   - Expect: one concrete system, not "everything."
   - Why: MCP earns its slot per-system, per-workflow — start from a real need.

2. **Read the example GitHub MCP config (no secrets).**
   - Open [`github-mcp.example.json`](github-mcp.example.json).
   - Expect: the token is referenced via `${GITHUB_PERSONAL_ACCESS_TOKEN}`, an
     environment variable — never a literal token string in the file.
   - > **Watch out:** if you ever see a real token typed directly into a config file
     > you're about to commit, stop and rotate that token — treat it as already leaked.

3. **Read the filesystem MCP note and decide if you need one.**
   - Open [`filesystem-note.md`](filesystem-note.md).
   - Expect: for most local-repo workflows, Claude Code's built-in file tools already
     cover it — a filesystem MCP server is for access *outside* the working directory.
   - Tip: this is the tool-sprawl question in miniature — "would the built-in tool do?"

4. **Document one MCP you would add — or wire GitHub if you have a token.**
   - Action (documentation path — always available):

     ```bash
     cd archive/helpers/free-claude-code/lessons
     mkdir -p artifacts/mcp
     ```

     Create `artifacts/mcp/proposed-mcp.md` with:
     - System: `<e.g. Jira, PagerDuty, Datadog>`
     - Why: `<the concrete workflow it unblocks — cite a real recent moment>`
     - Scope requested: `<read-only? which project/repo/org?>`
     - Tools you'd actually use: `<name 2–3 real ones, not "everything the server offers">`
   - Expect: a filled-in doc with no vague "would be nice to have" language — every
     line ties to a real workflow.

   - Action (live path — only if you have a GitHub personal access token you're allowed
     to use here):

     ```bash
     cp 05-mcp/github-mcp.example.json artifacts/mcp/github-mcp.local.json
     # edit artifacts/mcp/github-mcp.local.json if your server invocation differs
     export GITHUB_PERSONAL_ACCESS_TOKEN="<your token, set in your shell, never in the file>"
     ```

   - > **Important:** `artifacts/mcp/github-mcp.local.json` must never contain a literal
     > token. If your `.gitignore` doesn't already exclude `*.local.json`, add it before
     > you save anything real there.

5. **If you wired it live: call one real, read-only tool.**
   - Action: ask Claude to list open PRs on a repo you have access to, using the
     GitHub MCP tool rather than `gh` CLI.
   - Expect: a real, current list — proof the token and scope work.
   - Tip: start with a read-only call before ever trying a write-capable tool through MCP.

## Copy-paste templates

- [`github-mcp.example.json`](github-mcp.example.json) — config shape, secret via env var.
- [`filesystem-note.md`](filesystem-note.md) — when a filesystem MCP is (and isn't) worth it.

## How it works

Claude Code, as an MCP **client**, launches or connects to each configured MCP
**server** at startup and asks it for its tool/resource schemas. Those schemas — not
the server's internal implementation — are what gets added to context. When you ask for
something an MCP tool can satisfy, Claude Code picks the matching tool by schema (name
+ description + parameters, the same way it picks between built-in tools), calls it with
arguments, and gets a result back to reason over. The server enforces its own auth and
scope on every call — Claude Code has no ambient access beyond what the server's
configured credential allows.

## Pitfalls

- **Empty resources mistaken for "server down"** → many servers barely populate
  resources; the tools are the real surface. Fix: test with a tool call, not a resource
  read, before concluding anything is broken.
- **Token committed in a config file** → instant credential leak once pushed. Fix:
  always reference secrets via env vars; `.gitignore` any `*.local.json`.
- **Over-broad scope** ("token can write to every repo in the org") → one bad tool call
  has org-wide blast radius. Fix: scope tokens to the minimum repo/permission the
  workflow needs.
- **Tool sprawl** — five MCP servers connected "just in case" → every turn pays the
  context cost of all their tool schemas, and the model has more ways to pick wrong.
  Fix: connect only what a real, current workflow needs; disconnect what you added
  months ago and never use.
- **Confusing an MCP tool with a shell alternative that already exists** (e.g. GitHub
  MCP vs `gh` CLI) → redundant surface, redundant auth to manage. Fix: pick one path per
  system and stick to it.

## Knowledge check

1. What is the practical difference between an MCP "tool" and a "resource"?
   <br>**A:** Tools are callable actions; resources are readable data — in practice,
   tools are the more complete and more used surface for most servers.
2. Why should you never conclude an MCP server is broken just because its resources are
   empty?
   <br>**A:** Many servers implement tools fully but leave resources sparse or empty by
   design — test with a tool call before assuming failure.
3. Where should an MCP server's auth token live — in the JSON config or in an env var?
   <br>**A:** An environment variable, referenced from the config — never a literal
   value in a file you might commit.
4. What is "tool sprawl," and why is it a real, ongoing cost rather than a one-time one?
   <br>**A:** Every connected server's tool schemas load into context every turn;
   more servers connected means more tokens spent and more chances to pick the wrong
   tool, on every single message.
5. Give one concrete criterion for deciding whether a workflow deserves a new MCP server.
   <br>**A:** A real, recurring need that built-in tools or existing servers can't
   satisfy — not "might be nice to have."
6. What should scope look like for a token used by an MCP server, by default?
   <br>**A:** Minimum necessary — read-only where possible, limited to the specific
   repo/project/org the workflow actually touches.

## Acceptance criteria

- [ ] Example JSON + `artifacts/mcp/NOTES.md` completed
- [ ] Token storage plan does not include git or chat
- [ ] Live MCP optional — notes alone OK

## Recap

- **Built:** a documented MCP proposal (or a live, token-backed GitHub MCP connection)
  under `artifacts/mcp/`, scoped and justified against a real workflow.
- **Understand:** tools vs resources, why resources being empty isn't "down," scope and
  auth hygiene, and tool sprawl as an ongoing (not one-time) cost.
- **Can do next:** wire a hook (module 06) to enforce the guardrails MCP access alone
  can't — e.g. deny-listing dangerous tool calls regardless of which server offers them.

## Stretch

- If you wired GitHub MCP live, try a **write** tool (e.g. commenting on a PR) only
  after explicitly confirming scope and getting sign-off from yourself as if you were a
  reviewer approving that permission.
- Audit every MCP server currently connected in your environment: for each, name the
  real workflow it serves — disconnect any you can't name one for.

## Feedback

Could you explain, from memory, why a real GitHub token should never appear directly in
a JSON config file? If you tried the live path and a tool call failed, note the exact
error and whether it was a scope issue, an auth issue, or a wrong tool name — those are
three different fixes.

## Domain Stretch

> Optional, skippable. Meridian/IIQ mapping only.

This repo already wires an `identityiq` MCP server for live IIQ tool calls — see
`docs/api/MCP-TOOLS.md` and the always-applied rule about preferring MCP tools over
lab/`importdynamic` for live create/list/run requests. Same tools-over-resources lesson
applies: empty IIQ resources don't mean the server is down.
