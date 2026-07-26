# Lesson 05 — Account Correlation Mastery

**Level:** Intermediate  
**Prereq:** Lessons 02–04  
**Meridian story:** Accounts are orphaned when IIQ cannot match them to people. Correlation is how Meridian avoids “ghost” access floating unowned in audits.

---

## Story

HR usernames and IT usernames do not always match. Email is often the bridge. Some contractor accounts will never match—and that is a finding, not a failure.

You will tune correlation so `MNB-IT-Access` accounts attach to `MNB-HR` identities whenever possible, then review uncorrelated accounts.

---

## How it works

Correlation asks:

```text
For this account, which Identity (if any) owns it?
```

Typical strategies:

1. Exact match on `email`  
2. Exact match on `username` / `userName`  
3. Custom **correlation rule** (advanced)

Uncorrelated accounts appear in reports and are audit gold: either fix matching, or investigate orphaned access.

---

## Lesson goals

- [ ] Configure correlation for `MNB-IT-Access`
- [ ] Re-aggregate / refresh so links appear on identity cubes
- [ ] Produce a short list of uncorrelated accounts and explain each

---

## Tasks

### Task 1 — Baseline

1. Pick a user present in **both** files with the same email (ideal).  
2. Open their identity → Accounts tab.  
3. Note whether `MNB-IT-Access` is already linked.

### Task 2 — Configure correlation

On `MNB-IT-Access`:

1. Open correlation / account mapping settings.  
2. Prefer: account `email` → identity `email`.  
3. Secondary: account `userName` → identity `name` / `uid` / HR `userName` (depends on how you mapped HR).  
4. Save.

### Task 3 — Reprocess

1. Re-run `Aggregate MNB-IT-Access` (or a dedicated correlation refresh if you use one).  
2. Run `Refresh MNB Identities`.  
3. Re-open the test identity; confirm the IT account is linked and entitlements show.

### Task 4 — Hunt orphans

1. Use Advanced Analytics / Account search / Uncorrelated accounts report (whatever your build provides).  
2. List 3–5 uncorrelated accounts.  
3. For each, decide: data quality issue, missing HR record, or true orphan.

### Task 5 — Meridian control narrative

Write 5–7 sentences as if for an auditor:

> “Meridian correlates IT access accounts to HR identities primarily by email. Uncorrelated accounts are reviewed weekly…”

This narrative skill matters as much as clicking the UI.

---

## Tips & tricks

- Correlation problems are usually **data** problems. Fix the file or mapping before writing custom rules.  
- Be careful correlating only on first/last name—collisions create wrong ownership (bad in banking).  
- After changing correlation, you may need reaggregation + refresh; don’t expect magic mid-session without tasks.

---

## Checkpoint

1. What does an uncorrelated account mean?  
2. Why is email safer than display name?  
3. Should IT apps create identities? Why/why not?

---

## Stretch

Write a simple correlation rule that tries email first, then username. Import via Debug / console. Keep it tiny and commented.

**Next:** [Lesson 06 — Birthright roles for bankers](06-birthright-roles.md)
