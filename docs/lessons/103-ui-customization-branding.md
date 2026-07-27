# Lesson 103 — UI Customization & Branding

| Field | Value |
| --- | --- |
| **Level** | Intermediate |
| **Track** | Plugins, APIs & SSD |
| **Time** | 60–75 minutes |
| **Prereq** | [Lesson 102 — Custom Java Services](102-custom-java-services.md); Lesson 95 QuickLinks |
| **Lab data** | `web/` overlays; plugin CSS examples in `pluginsrc/*/ui/css/`; [docs/SSD.md](../SSD.md) |

## Learning objectives

You will be able to:

- Identify IIQ branding surfaces: login page, headers, messages, UIConfig
- Apply Meridian-safe branding (bank name, environment banner) without breaking accessibility
- Override or add a message key for a Meridian label
- Place static assets via `web/` SSB overlay or plugin stylesheet
- Separate **lab** vs **prod** visual cues so operators never confuse environments

## Why this matters

Operators approve wire-adjacent access in the same browser they use for email. If sandbox looks identical to production, wrong-environment changes are inevitable. Branding is a safety control, not decoration.

**Control / audit:** Environment banners and naming standards reduce change errors. Custom JS that alters approval semantics is a governed plugin (Lessons 97–98)—not a stealth `web/` hack.

## Concepts

| Surface | Mechanism | Meridian guidance |
| --- | --- | --- |
| Login / header text | UIConfig, message properties, branding files | Show **SANDBOX** / **PROD** clearly |
| Labels / text | Message catalog keys | Prefer keys over hardcoded page text |
| CSS / logos | `web/` overlay or plugin `ui/css` | Keep contrast WCAG-friendly |
| Behavior changes | Plugin snippets + rights | Never silent-approve via JS |

```text
  Operator opens IIQ
        |
        v
  [ENV BANNER: MNB SANDBOX]  <--- required lab cue
        |
        v
  Standard menus (capabilities)
        |
        +-- Plugin snippets (gated)
        +-- QuickLinks (gated)
```

**SSD path:** Custom static files and JSP/XHTML overlays belong in `web/` and are baked by `./build.sh war`. Prefer small overlays; prefer plugins for page-specific behavior.

## Before you start

- [ ] Know whether you can rebuild WAR or only change messages via Debug/UI
- [ ] Screenshot “before” login page
- [ ] Lesson 96: only admins change UIConfig
- [ ] Agree Meridian banner text: `Meridian National Bank — SANDBOX` (lab)

## Lab procedure

### Task 1 — Baseline screenshots

1. Open login page; screenshot.
2. Open home after login as `spadmin`; screenshot header/footer.
3. Note any existing environment indicator.

**Expected result:** Before images in binder.

### Task 2 — Environment banner / product name

1. Locate branding or UIConfig settings for product name / header (Gear → Global Settings / UIConfig or equivalent).
2. Set display text to include **SANDBOX** (lab) or document property-token approach for env-specific banners.
3. Save; hard-refresh browser.
4. Confirm banner visible without inspecting HTML.

**Expected result:** Unmistakable SANDBOX (or env) cue on primary UI.

**If it fails:** Use login page message customization or a QuickLink HTML note as temporary cue; still record target end-state.

### Task 3 — Message key change

1. Find Message catalog / debug messages (or `message` properties overlay in `web/`).
2. Add or override a key such as Meridian welcome / work item empty-state text—keep professional tone.
3. Prefer `MNB_` prefix in custom keys.
4. Reload and show the string in UI.

**Expected result:** One custom Meridian message key visible.

**If it fails:** Document key name and intended value in `config/` notes for later bake.

### Task 4 — CSS overlay or plugin stylesheet study

1. Open `pluginsrc/AccessRequestApprovalAddins/ui/css/AccessRequestApprovalAddins.css` as a pattern.
2. Either: add a minimal `web/` CSS that styles the env banner, **or** document the file you would add (`web/css/mnb-branding.css`).
3. Rule: do not hide required legal/approval text; do not remove cert decision buttons via CSS.

**Expected result:** CSS path chosen + “do not hide controls” rule written.

### Task 5 — Prod look-alike danger test

1. Write a three-line standard: Prod banner red/high-contrast “PROD”; Sandbox amber “SANDBOX”; Dev blue “DEV” (colors optional—clarity mandatory).
2. Confirm tokens in `sandbox` vs `prod` properties would differ for banner text.
3. Get peer to identify environment from screenshot alone.

**Expected result:** Peer correctly identifies sandbox from banner.

### Task 6 — Change control note

1. Record: UI branding changes promote via SSB like XML (Lesson 101).
2. List owners: IAM UX/`helen.ross` + CAB for prod banner changes.
3. Explicitly forbid behavior-changing JS in `web/` without plugin review.

**Expected result:** Change-control paragraph in binder.

## Acceptance criteria

- [ ] Before/after screenshots
- [ ] Environment banner or documented equivalent cue
- [ ] One Meridian message key customized or staged
- [ ] CSS overlay plan with safety rule
- [ ] Peer environment-ID test passed
- [ ] Promotion path referenced to SSB

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Banner not showing | Cache / CDN | Hard refresh; restart app if baked resource |
| Message key ignored | Wrong bundle / typo | Match exact key; check locale |
| CSS breaks layout | Over-broad selectors | Scope under Meridian class/banner id |
| Prod/sandbox confusion | Same banner text | Tokenize per env immediately |
| Unauthorized UIConfig edit | Capability | Restrict to SystemAdministrator / designated |

## Training binder evidence

- Before/after login + home screenshots  
- Message key name/value  
- Banner standard (SANDBOX/DEV/PROD)  
- Change-control note  

## Knowledge check

1. Why must sandbox not look like production?
2. Where do SSB UI overlays live?
3. When should you use a plugin snippet instead of `web/` JS?
4. Who owns prod branding changes?
5. What must custom CSS never hide?

### Answers

1. Prevents wrong-environment administration and irreversible prod changes.  
2. `web/` (baked into WAR).  
3. Page-specific behavior with versioning, rights, and install XML—governed extensions.  
4. IAM lead with CAB; not ad-hoc operator taste.  
5. Approval/certification controls or required legal/decision text.

## Stretch lab

Draft `web/` overlay mock for Meridian favicon + login subtitle “Authorized users only — activity audited.”

## Summary

- Branding is an operational safety control for multi-env Meridian.
- Prefer tokens + SSB overlays; gate behavior changes as plugins.
- Prove env identity with screenshots and peer checks.

## Accessibility & trust cues

1. Banner text must remain readable at 200% zoom.
2. Color alone is insufficient—include the word `SANDBOX` / `PROD`.
3. Login subtitle should state monitoring: activity audited.
4. Do not auto-dismiss banners via JS timers.

### Task 7 — Message bundle localization note

1. If lab uses only `en_US`, still namespace keys with `MNB_`.
2. Document that prod may require legal-approved language for login warnings.
3. Export customized messages into `web/` or config-controlled properties for SSB.

**Expected result:** Localization/ownership note.

### Anti-patterns gallery

| Anti-pattern | Risk |
| --- | --- |
| Custom JS auto-approves work items | Control bypass |
| Hide revoke button with CSS | Failed certs |
| Same logo/banner all envs | Wrong-env edits |
| Unreviewed third-party JS CDN | Supply chain |

## SSB bake verification

After branding files land in `web/`:

1. `./build.sh -Dtarget=sandbox clean war`
2. Deploy or refresh lab
3. Hard-refresh browser; confirm banner + message key
4. Commit only `web/` sources—not exploded `build/`

Homelab: thin app image rebuild per [HOMELAB-CD.md](../HOMELAB-CD.md) when `web/` changes.

### QuickLink branding vs global branding

Global banners protect every operator. QuickLinks (Lesson 95) are optional entry points and must not be the only env cue. If QuickLink text says SANDBOX but login does not, fix login first.

---

**Previous:** [Lesson 102 — Custom Java Services](102-custom-java-services.md)  
**Next:** [Lesson 104 — AuditConfig & SIEM](104-auditconfig-and-siem.md)
