# Lesson Quiz — Question Bank

5–8 questions per module. Fields: Category, Question, Options, Correct, Explanation, Review.

Default quiz length: **5 questions** (token-aware).

---

## Lesson 01: Slash Commands

### Q1
- **Category**: conceptual
- **Question**: What is a slash command in Claude Code?
- **Options**: A) A shell alias in zsh | B) A user-invoked shortcut that steers Claude for a repeatable task | C) An MCP server name | D) A git hook
- **Correct**: B
- **Explanation**: Slash commands (including skills exposed as `/name`) are shortcuts you invoke in-session for a known workflow.
- **Review**: Concept primer

### Q2
- **Category**: practical
- **Question**: Where should project-shared skill shortcuts live?
- **Options**: A) Only in ~/.zshrc | B) In the team's wiki | C) Under the project's `.claude/skills/` (or legacy `.claude/commands/`) | D) In /tmp
- **Correct**: C
- **Explanation**: Project skills travel with the repo so the team shares the same shortcuts.
- **Review**: Hands-on install

### Q3
- **Category**: practical
- **Question**: How do you pass all text after `/pr` into the skill body?
- **Options**: A) `$INPUT` | B) `$ARGUMENTS` | C) `$@` | D) `%*`
- **Correct**: B
- **Explanation**: `$ARGUMENTS` captures everything after the command name.
- **Review**: Arguments

### Q4
- **Category**: judgment
- **Question**: A teammate wants one mega `/do-everything` command for review, deploy, and incident response. What should you recommend?
- **Options**: A) Build it — fewer commands is always better | B) Split into focused commands/skills with clear triggers | C) Put it all in CLAUDE.md only | D) Use only MCP
- **Correct**: B
- **Explanation**: Staff practice is one job per skill/command so triggers stay sharp and failures stay diagnosable.
- **Review**: Why this matters / pitfalls

### Q5
- **Category**: conceptual
- **Question**: Skills as `/name` vs legacy `.claude/commands/*.md` — which takes precedence when names collide?
- **Options**: A) Legacy commands | B) Skills | C) Whichever file is newer | D) Claude asks every time
- **Correct**: B
- **Explanation**: Skills supersede legacy commands with the same name.
- **Review**: Concept primer

---

## Lesson 02: Memory

### Q1
- **Category**: conceptual
- **Question**: What problem does `CLAUDE.md` solve?
- **Options**: A) Replacing CI | B) Persisting project standards and context across sessions | C) Storing API keys | D) Compiling TypeScript
- **Correct**: B
- **Explanation**: Memory files load automatically so you stop re-explaining build commands and invariants.
- **Review**: Concept primer

### Q2
- **Category**: practical
- **Question**: Where do personal preferences that should NOT be committed usually live?
- **Options**: A) In the public README | B) Personal Claude memory (e.g. ~/.claude/CLAUDE.md) or local-only files | C) In production secrets manager as plaintext in git | D) In the PR title
- **Correct**: B
- **Explanation**: Keep personal taste out of the team CLAUDE.md; use personal/local memory.
- **Review**: Hierarchy

### Q3
- **Category**: judgment
- **Question**: Your CLAUDE.md is 4,000 lines of every historical decision. What is the staff fix?
- **Options**: A) Add more detail | B) Slim to high-signal invariants; link deeper docs | C) Delete all memory | D) Put secrets in it to save space elsewhere
- **Correct**: B
- **Explanation**: Context is a budget — memory should be high-signal, not a second wiki dump.
- **Review**: Context budget

### Q4
- **Category**: practical
- **Question**: Directory-scoped memory is useful when:
- **Options**: A) You never use monorepos | B) One subtree (e.g. `services/api`) needs different rules than the rest | C) You want to hide memory from Claude | D) You are avoiding git
- **Correct**: B
- **Explanation**: Path-specific instructions keep global memory small and local rules precise.
- **Review**: Hands-on

### Q5
- **Category**: safety
- **Question**: Should API keys go in CLAUDE.md?
- **Options**: A) Yes, for convenience | B) Never — memory is not a secret store | C) Only if base64 encoded | D) Only on Fridays
- **Correct**: B
- **Explanation**: Secrets never belong in memory files or chat.
- **Review**: Pitfalls

---

## Lesson 03: Skills

### Q1
- **Category**: conceptual
- **Question**: What is progressive disclosure in a skill?
- **Options**: A) Loading every file always | B) Keeping SKILL.md lean and pulling reference/scripts only when needed | C) Hiding the skill from the user | D) Using only YAML with no body
- **Correct**: B
- **Explanation**: Progressive disclosure saves context while keeping deep procedures available.
- **Review**: Concept primer

### Q2
- **Category**: practical
- **Question**: The skill `description` frontmatter is primarily for:
- **Options**: A) Humans only | B) Triggering / routing — when Claude should load the skill | C) npm publish | D) Docker labels
- **Correct**: B
- **Explanation**: Good descriptions include when-to-use keywords so auto-invocation works.
- **Review**: Trigger design

### Q3
- **Category**: judgment
- **Question**: Personal vs project skill — team naming conventions belong where?
- **Options**: A) Only in personal skills | B) Project `.claude/skills/` so the repo owns them | C) Slack pins | D) Random gist
- **Correct**: B
- **Explanation**: Shared engineering truth lives in-repo.
- **Review**: Scope table

### Q4
- **Category**: practical
- **Question**: A skill that tries to review PRs, rotate secrets, and deploy is:
- **Options**: A) Ideal | B) An anti-pattern — split by job | C) Required by Claude | D) The same as a hook
- **Correct**: B
- **Explanation**: One job per skill.
- **Review**: Pitfalls

### Q5
- **Category**: conceptual
- **Question**: How do you evaluate a skill before promoting it?
- **Options**: A) Never test it | B) Run it on a real task, check trigger accuracy and output contract, keep evidence in artifacts | C) Only read the YAML | D) Ask marketing
- **Correct**: B
- **Explanation**: Skills earn their place by working under real prompts.
- **Review**: Lab / acceptance

---

## Lesson 04: Subagents

### Q1
- **Category**: conceptual
- **Question**: Why use a subagent instead of one long main-thread prompt?
- **Options**: A) Subagents are free | B) Isolated context and specialized instructions improve focus | C) Subagents cannot read files | D) To avoid CLAUDE.md
- **Correct**: B
- **Explanation**: Isolation keeps the main conversation clean and specialists sharp.
- **Review**: Concept primer

### Q2
- **Category**: judgment
- **Question**: Best split for “review this PR”?
- **Options**: A) One agent that also deploys prod | B) Separate reviewer vs test-focused agents with clear scopes | C) No agents — only hooks | D) Ten agents for every file
- **Correct**: B
- **Explanation**: Narrow specialists beat a mega-agent.
- **Review**: Why this matters

### Q3
- **Category**: practical
- **Question**: Where do custom agent definitions typically live?
- **Options**: A) `.claude/agents/` | B) `/etc/agents` | C) Only in ChatGPT | D) In node_modules
- **Correct**: A
- **Explanation**: Project agents are versioned under `.claude/agents/`.
- **Review**: Hands-on

### Q4
- **Category**: safety
- **Question**: A security-review subagent should often:
- **Options**: A) Have write+deploy to prod by default | B) Prefer read-only / limited tools | C) Skip CLAUDE.md | D) Print secrets for convenience
- **Correct**: B
- **Explanation**: Least privilege for high-risk reviews.
- **Review**: Pitfalls

### Q5
- **Category**: conceptual
- **Question**: Subagents vs skills — rough distinction?
- **Options**: A) Identical | B) Skills teach workflows; subagents are delegated assistants with their own context | C) Subagents replace MCP | D) Skills only work offline
- **Correct**: B
- **Explanation**: Complementary primitives — compose them deliberately.
- **Review**: How it works

---

## Lesson 05: MCP

### Q1
- **Category**: conceptual
- **Question**: What does MCP provide Claude Code?
- **Options**: A) A new programming language | B) A standard way to expose external tools/data sources | C) Free cloud GPUs | D) Automatic production deploys
- **Correct**: B
- **Explanation**: Model Context Protocol connects live tools (GitHub, Jira, DBs, etc.).
- **Review**: Concept primer

### Q2
- **Category**: safety
- **Question**: Where should MCP auth tokens live?
- **Options**: A) In committed JSON | B) Environment / secret store — never in git or chat | C) In CLAUDE.md | D) In PR descriptions
- **Correct**: B
- **Explanation**: Config examples omit secrets; real tokens stay out of the repo.
- **Review**: Pitfalls

### Q3
- **Category**: judgment
- **Question**: Enabling every MCP server you find is:
- **Options**: A) Best practice | B) Tool sprawl — enable what you need with clear scopes | C) Required for slash commands | D) Faster than skills
- **Correct**: B
- **Explanation**: More tools mean more attack surface and noisier routing.
- **Review**: Why this matters

### Q4
- **Category**: practical
- **Question**: A safe artifact for this curriculum is:
- **Options**: A) `github-mcp.example.json` with placeholders | B) A file containing a live PAT | C) A screenshot of your password manager | D) Production DB credentials
- **Correct**: A
- **Explanation**: Examples use placeholders only.
- **Review**: Lab

### Q5
- **Category**: conceptual
- **Question**: MCP vs hooks:
- **Options**: A) Same thing | B) MCP exposes tools; hooks react to Claude Code events | C) Hooks replace MCP | D) MCP only formats code
- **Correct**: B
- **Explanation**: Different layers — integrate, don't conflate.
- **Review**: How it works

---

## Lesson 06: Hooks

### Q1
- **Category**: conceptual
- **Question**: What are hooks?
- **Options**: A) Git commit messages | B) Event-driven actions that run around Claude tool use / session events | C) MCP prompts | D) CSS animations
- **Correct**: B
- **Explanation**: Hooks automate validation and guardrails.
- **Review**: Concept primer

### Q2
- **Category**: judgment
- **Question**: “Please don't commit secrets” in CLAUDE.md vs a PreToolUse deny hook:
- **Options**: A) Memory alone is enough | B) Deny hooks beat hope — enforce mechanically | C) Hooks cannot see Bash | D) Only PostToolUse matters for secrets
- **Correct**: B
- **Explanation**: Staff posture: deny > hope.
- **Review**: Why this matters

### Q3
- **Category**: practical
- **Question**: Blocking edits under a protected path is best done with:
- **Options**: A) A sticky note | B) A matcher + deny/block hook on Write/Edit | C) Renaming the folder weekly | D) Disabling Claude forever
- **Correct**: B
- **Explanation**: Path matchers + deny rules encode policy.
- **Review**: Hands-on

### Q4
- **Category**: safety
- **Question**: A secret-scanning hook should:
- **Options**: A) Echo the secret into logs for debugging | B) Fail closed without printing the secret value | C) Upload secrets to a public gist | D) Store secrets in the hook script
- **Correct**: B
- **Explanation**: Never re-leak secrets in denial messages or logs.
- **Review**: Pitfalls

### Q5
- **Category**: conceptual
- **Question**: PreToolUse vs PostToolUse:
- **Options**: A) Pre runs after the tool; Post before | B) Pre can block/validate before the tool; Post reacts after | C) They are identical | D) Only Pre exists
- **Correct**: B
- **Explanation**: Timing determines whether you can prevent damage.
- **Review**: Concept primer

---

## Lesson 07: Plugins

### Q1
- **Category**: conceptual
- **Question**: A plugin in Claude Code is best described as:
- **Options**: A) A single shell alias | B) A distributable bundle of related skills/agents/hooks/MCP bits | C) A replacement for git | D) Only a VS Code theme
- **Correct**: B
- **Explanation**: Plugins package a workflow for a team.
- **Review**: Concept primer

### Q2
- **Category**: judgment
- **Question**: When should you keep a skill separate instead of bundling a plugin?
- **Options**: A) Always bundle everything | B) When the skill is useful alone and the rest is not shared | C) Never use skills | D) Only on weekends
- **Correct**: B
- **Explanation**: Bundle when the pieces are co-required; otherwise keep surface small.
- **Review**: Why this matters

### Q3
- **Category**: practical
- **Question**: A staff-quality plugin sketch should document:
- **Options**: A) Only the logo | B) Included commands, agents, hooks, and install steps | C) Production passwords | D) Nothing — plugins are self-describing always
- **Correct**: B
- **Explanation**: Distribution needs a clear contract.
- **Review**: Lab

### Q4
- **Category**: conceptual
- **Question**: Plugins vs copying skills manually:
- **Options**: A) Plugins help standardize team install | B) Manual copy is always superior for teams of 50 | C) Plugins delete CLAUDE.md | D) No difference
- **Correct**: A
- **Explanation**: Plugins reduce drift across machines.
- **Review**: How it works

### Q5
- **Category**: safety
- **Question**: Should a plugin ship live cloud credentials?
- **Options**: A) Yes | B) No — document env vars; never embed secrets | C) Only if encrypted with ROT13 | D) Only in the README title
- **Correct**: B
- **Explanation**: Same secret rules as everything else.
- **Review**: Pitfalls

---

## Lesson 08: Checkpoints

### Q1
- **Category**: conceptual
- **Question**: What is a checkpoint for?
- **Options**: A) Deploying to prod | B) Snapshotting conversation/code state so you can rewind experiments | C) Compressing context permanently without choice | D) Installing MCP
- **Correct**: B
- **Explanation**: Checkpoints make exploration reversible.
- **Review**: Concept primer

### Q2
- **Category**: practical
- **Question**: A common way to open rewind is:
- **Options**: A) `rm -rf /` | B) Esc Esc or `/rewind` (per current Claude Code UX) | C) Only by rebooting | D) Deleting .git
- **Correct**: B
- **Explanation**: Rewind UI restores prior points; confirm which layers (code vs conversation) you restore.
- **Review**: Hands-on

### Q3
- **Category**: judgment
- **Question**: Best use of checkpoints for staff work:
- **Options**: A) Skip planning and thrash blindly | B) Try an approach, rewind, compare alternatives safely | C) Avoid version control forever | D) Store secrets in checkpoint names
- **Correct**: B
- **Explanation**: Pair with git; checkpoints are session safety, not a VCS replacement.
- **Review**: Why this matters

### Q4
- **Category**: conceptual
- **Question**: Checkpoints replace git?
- **Options**: A) Yes | B) No — still commit meaningfully; checkpoints are session-level | C) Only on main | D) Only for binary assets
- **Correct**: B
- **Explanation**: Different layers of undo.
- **Review**: Pitfalls

### Q5
- **Category**: practical
- **Question**: After a failed experiment you should:
- **Options**: A) Leave broken files and start a new chat only | B) Rewind or restore intentionally, then note what you learned | C) Force-push always | D) Disable all permissions forever
- **Correct**: B
- **Explanation**: Close the loop: restore + capture learning.
- **Review**: Lab

---

## Lesson 09: Advanced

### Q1
- **Category**: conceptual
- **Question**: Plan mode is most valuable when:
- **Options**: A) Renaming a typo | B) Multi-file risky changes need a design before edits | C) You want to skip tests | D) Printing help text
- **Correct**: B
- **Explanation**: Plan first reduces thrash and blast radius.
- **Review**: Concept primer

### Q2
- **Category**: practical
- **Question**: Permission modes exist to:
- **Options**: A) Decorate the UI | B) Control how aggressively Claude may run tools without asking | C) Replace IAM systems | D) Compile Java
- **Correct**: B
- **Explanation**: Choose modes deliberately for the environment (laptop vs CI).
- **Review**: Hands-on

### Q3
- **Category**: judgment
- **Question**: `bypassPermissions` in a shared prod-adjacent repo is:
- **Options**: A) Always fine | B) High risk — reserve for tightly controlled contexts | C) Required for skills | D) The same as plan mode
- **Correct**: B
- **Explanation**: Staff default is least privilege.
- **Review**: Pitfalls

### Q4
- **Category**: conceptual
- **Question**: Background tasks help when:
- **Options**: A) You need long work without blocking the main thread of interaction | B) You want to hide failures | C) Tokens are free forever | D) You dislike logs
- **Correct**: A
- **Explanation**: Use for long builds/tests while you continue.
- **Review**: How it works

### Q5
- **Category**: practical
- **Question**: A plan-first runbook artifact should include:
- **Options**: A) Only vibes | B) Goal, constraints, steps, verify commands, rollback notes | C) Production passwords | D) Unrelated memes only
- **Correct**: B
- **Explanation**: Make the plan executable and reviewable.
- **Review**: Lab

---

## Lesson 10: CLI

### Q1
- **Category**: conceptual
- **Question**: `claude -p` is primarily for:
- **Options**: A) Interactive REPL only | B) Non-interactive/print mode for scripts and CI | C) Painting images | D) Editing settings.json exclusively
- **Correct**: B
- **Explanation**: Headless invocations power automation.
- **Review**: Concept primer

### Q2
- **Category**: practical
- **Question**: Piping a log into Claude is useful to:
- **Options**: A) Upload secrets to Twitter | B) Explain or summarize stdin content without a long chat session | C) Bypass all hooks permanently | D) Format disks
- **Correct**: B
- **Explanation**: `cat file | claude -p "..."` is a classic pattern.
- **Review**: Hands-on

### Q3
- **Category**: judgment
- **Question**: In CI, you should:
- **Options**: A) Pass production secrets as prompt text | B) Scope prompts, redact secrets, pin permissions carefully | C) Use bypassPermissions on all jobs | D) Disable logging always
- **Correct**: B
- **Explanation**: Headless ≠ careless.
- **Review**: Pitfalls

### Q4
- **Category**: practical
- **Question**: Session resume helps when:
- **Options**: A) You never want continuity | B) You continue prior work without re-seeding all context | C) You delete the repo | D) MCP is disabled
- **Correct**: B
- **Explanation**: Resume/named sessions support multi-day work.
- **Review**: How it works

### Q5
- **Category**: conceptual
- **Question**: JSON output flags are useful because:
- **Options**: A) Humans hate JSON | B) Scripts can parse structured results | C) It disables the model | D) It removes the need for skills
- **Correct**: B
- **Explanation**: Machine-readable output enables pipelines.
- **Review**: Concept primer

---

## Lesson 11: Ops Playbooks

### Q1
- **Category**: judgment
- **Question**: A strong PR-review playbook combines:
- **Options**: A) Only emojis | B) Skill checklist + specialist agent(s) + guardrail hooks + optional MCP | C) MCP alone with no standards | D) Checkpoints only
- **Correct**: B
- **Explanation**: Composition is the staff move.
- **Review**: pr-review-pipeline

### Q2
- **Category**: practical
- **Question**: Incident triage packs should optimize for:
- **Options**: A) Long essays | B) Fast, ordered steps with verify commands under stress | C) Perfect prose | D) Ignoring logs
- **Correct**: B
- **Explanation**: On-call needs brevity and proof.
- **Review**: incident-triage

### Q3
- **Category**: safety
- **Question**: Release guardrails should:
- **Options**: A) Skip tests if demos look good | B) Encode pre-release checks and stop-ships mechanically where possible | C) Store release keys in the playbook markdown | D) Only run on developer laptops never CI
- **Correct**: B
- **Explanation**: Make the dangerous path hard.
- **Review**: release-guardrails

### Q4
- **Category**: conceptual
- **Question**: Why keep playbooks under `artifacts/` first?
- **Options**: A) To hide them | B) Iterate safely before promoting into team `.claude/` paths | C) Artifacts are encrypted automatically | D) Git ignores them always
- **Correct**: B
- **Explanation**: Draft → prove → promote.
- **Review**: Capstone

### Q5
- **Category**: judgment
- **Question**: Teach-back proves mastery by:
- **Options**: A) Claiming you read the README | B) Demonstrating the composed pack live with evidence | C) Starring the repo | D) Disabling all hooks
- **Correct**: B
- **Explanation**: Show the workflow under a realistic scenario.
- **Review**: Capstone
