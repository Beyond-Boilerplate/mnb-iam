# Day 22 — MCP Fundamentals

| Field | Value |
| --- | --- |
| **Week** | 4 — MCPs + Capstone |
| **Time** | 2.5–3 hours |
| **Prereq** | Week 3 playbook |
| **Artifacts** | `artifacts/mcp/README.md` |

## Learning objectives

You will be able to:

- Explain MCP (Model Context Protocol) as **tool servers** Claude can call
- Add, auth, list, and disable MCPs safely
- Design least-privilege scopes for IAM work
- Plan Meridian MCP set: Jira, GitHub, iiq-verify (custom)

## IAM pain (today’s tax)

Copy-paste between Jira, GitHub, IIQ UI, and terminal is the hidden full-time job. MCPs make those systems addressable to the agent — with blast radius you must control.

## Claude concept

```text
Claude Code
  ├─ built-in tools (files, shell)
  └─ MCP servers
        ├─ jira (tickets)
        ├─ github (PRs)
        └─ iiq-verify (lab asserts)
```

Rules:

1. **Auth is user-bound** — treat tokens like prod credentials  
2. **Prefer read scopes first**  
3. **Hooks can gate MCP calls** (beforeMCPExecution patterns)  
4. Never MCP prod IIQ write APIs without CAB-grade controls  

## Before you start

- [ ] Claude Code MCP docs for your version available  
- [ ] Willingness to connect ≤1 remote MCP today (or mock)  

## Lab procedure

### Task 1 — Inventory

Document how you add MCPs (`claude mcp add` or UI). Write examples in README.

### Task 2 — Local dry conceptual design

For each planned server: tools you want / tools you refuse / data classes (PII!).

### Task 3 — Connect one low-risk MCP

Filesystem or GitHub read-only if available — or follow Day 23 Jira early if ready. Goal: `/mcp` shows connected.

### Task 4 — Threat model

1-pager: stolen token impact; ticket data residency; logging redaction.

## Deliverable

`artifacts/mcp/README.md` + `THREAT-MODEL.md`

## Acceptance criteria

- [ ] MCP mental model diagram in README  
- [ ] Least-privilege plan for 3 servers  
- [ ] At least one MCP connected OR sandbox/mock with documented blockers  
- [ ] Threat model lists PII handling  

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Auth loops | Re-auth; check org SSO allowlisting |
| Tools missing | Server capabilities / scopes |

## Stretch

- Draft hook policy for MCP write tools  
- Compare Cursor MCP config vs Claude Code  

## Knowledge check

1. MCP vs skill?  
2. Why read-first scopes?  
3. Should lab credentials go in MCP env committed to git?

### Answers

1. MCP = live external tools; skill = instructions.  
2. Limit blast radius while learning.  
3. Never commit — use secret stores / env / Keychain.

## Navigation

[← Day 21](day-21-agent-teams-orchestration.md) · [Day 23 →](day-23-mcp-jira-ticket-bridge.md)
