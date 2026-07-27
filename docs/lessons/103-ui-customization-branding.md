# Lesson 103 — UI Customization & Branding

**Level:** Intermediate  
**Track:** Plugins, APIs & SSD  
**Time:** 60–75 min  
**Prereq:** Lesson 102 — Custom Java Services; Lesson 95 QuickLinks  

**Lab data:**
- `web/` overlays; plugin CSS examples in `pluginsrc/*/ui/css/`
- [docs/SSD.md](../SSD.md)

---

## Learning objectives

You will be able to:

- Identify IIQ branding surfaces: login page, headers, messages, UIConfig
- Apply Meridian-safe branding (bank name, environment banner) without breaking accessibility
- Override or add a message key for a Meridian label
- Place static assets via `web/` SSB overlay or plugin stylesheet
- Separate **lab** vs **prod** visual cues so operators never confuse environments
- Forbid behavior-changing JS in `web/` without plugin governance (Lessons 97–98)

---

## Why this matters

**Business.** Operators approve wire-adjacent access in the same browser they use for email. If sandbox looks identical to production, wrong-environment changes are inevitable. Last year a Meridian engineer revoked a cert decision thinking they were in SANDBOX — they were in a look-alike host. Branding is a safety control, not decoration.

**Control / audit.** Environment banners and naming standards reduce change errors. Custom JS that alters approval semantics is a governed plugin (Lessons 97–98) — not a stealth `web/` hack. Examiners ask how you prevent wrong-system administration; “we train people carefully” is weaker than “PROD banner is unmistakable and tokenized per env.”

---

## Concepts

### Branding surfaces

| Surface | Mechanism | Meridian guidance |
| --- | --- | --- |
| Login / header text | UIConfig, message properties, branding files | Show **SANDBOX** / **PROD** clearly |
| Labels / text | Message catalog keys | Prefer keys over hardcoded page text; prefix `MNB_` |
| CSS / logos | `web/` overlay or plugin `ui/css` | Keep contrast WCAG-friendly |
| Behavior changes | Plugin snippets + rights | Never silent-approve via JS |

### Environment banner standard

| Env | Banner cue | Color guidance (optional) |
| --- | --- | --- |
| Sandbox / lab | `Meridian National Bank — SANDBOX` | Amber / high visibility |
| Dev | `… — DEV` | Blue |
| Prod | `… — PROD` | Red / high contrast |

**Color alone is insufficient** — include the word `SANDBOX` / `PROD`. Banner text must remain readable at 200% zoom. Do not auto-dismiss banners via JS timers.

### Real-life Meridian example

A QuickLink label said “SANDBOX tools” but the login page showed only the Meridian logo. Contractors and ops still confused hosts. Fix: global banner on login + home first; QuickLinks (Lesson 95) are optional entry points and must not be the only env cue.

### Anti-patterns gallery

| Anti-pattern | Risk |
| --- | --- |
| Custom JS auto-approves work items | Control bypass |
| Hide revoke button with CSS | Failed certs / examiner finding |
| Same logo/banner all envs | Wrong-env edits |
| Unreviewed third-party JS CDN | Supply chain |
| Behavior change buried in `web/` JSP | No versioning / rights / install XML |

**SSD path:** Custom static files and JSP/XHTML overlays belong in `web/` and are baked by `./build.sh war`. Prefer small overlays; prefer plugins for page-specific behavior.

---

## How it works

```
  Operator opens IIQ
        │
        ▼
  [ENV BANNER: MNB SANDBOX]  <--- required lab cue (tokenized per SPTARGET)
        │
        ▼
  Standard menus (capabilities — Lesson 96)
        │
        ├── Plugin snippets (gated)
        └── QuickLinks (gated — Lesson 95)
```

| Change type | Promote how (Lesson 101) |
| --- | --- |
| Message keys / `web/` CSS | Rebuild WAR; deploy |
| UIConfig XML if exported | `config/` + tokens for banner text |
| Plugin CSS | Plugin bake / version bump |

Homelab: thin app image rebuild per [HOMELAB-CD.md](../HOMELAB-CD.md) when `web/` changes.

---

## Real-world setup (branding as ops safety)

### Step 1 — Baseline before you paint

1. Screenshot login + home “before.”
2. Note any existing environment indicator.
3. Agree Meridian banner text: `Meridian National Bank — SANDBOX` (lab).

### Step 2 — Tokenize per environment

1. Banner text differs in `sandbox` vs `prod` properties (`%%MNB_BANNER%%` or equivalent).
2. Never hard-code PROD string into a single shared file without tokens.

### Step 3 — Accessibility & trust cues

1. Readable at 200% zoom; word labels not color-only.
2. Login subtitle: authorized users only — activity audited.
3. Legal-approved language for prod login warnings (Compliance).

### Step 4 — Change control

1. Owners: IAM UX / `helen.ross` + CAB for prod banner changes.
2. Forbid behavior-changing JS in `web/` without plugin review.

---

## Before you start

- [ ] Know whether you can rebuild WAR or only change messages via Debug/UI
- [ ] Screenshot “before” login page
- [ ] Lesson 96: only admins change UIConfig
- [ ] Agree Meridian banner text: `Meridian National Bank — SANDBOX` (lab)
- [ ] Binder: `ui/branding/`

---

## Lab procedure

### Task 1 — Baseline screenshots

You cannot prove improvement without before images.

1. Open login page; screenshot.
2. Open home after login as `spadmin`; screenshot header/footer.
3. Note any existing environment indicator.

**Expected result:** Before images in binder.

### Task 2 — Environment banner / product name

This is the primary wrong-env control.

1. Locate branding or UIConfig settings for product name / header (Gear → Global Settings / UIConfig or equivalent).
2. Set display text to include **SANDBOX** (lab) or document property-token approach for env-specific banners.
3. Save; hard-refresh browser.
4. Confirm banner visible without inspecting HTML.

**Expected result:** Unmistakable SANDBOX (or env) cue on primary UI.

**If it fails:** Use login page message customization or a QuickLink HTML note as temporary cue; still record target end-state.

### Task 3 — Message key change

Prefer catalog keys so localization and SSB overlays stay coherent.

1. Find Message catalog / debug messages (or `message` properties overlay in `web/`).
2. Add or override a key such as Meridian welcome / work item empty-state text — keep professional tone.
3. Prefer `MNB_` prefix in custom keys.
4. Reload and show the string in UI.

**Expected result:** One custom Meridian message key visible.

**If it fails:** Document key name and intended value in `config/` notes for later bake.

### Task 4 — CSS overlay or plugin stylesheet study

1. Open a plugin CSS pattern such as `pluginsrc/AccessRequestApprovalAddins/ui/css/AccessRequestApprovalAddins.css` if present.
2. Either: add a minimal `web/` CSS that styles the env banner, **or** document the file you would add (`web/css/mnb-branding.css`).
3. Rule: do not hide required legal/approval text; do not remove cert decision buttons via CSS.

**Expected result:** CSS path chosen + “do not hide controls” rule written.

### Task 5 — Prod look-alike danger test

1. Write a three-line standard: Prod banner red/high-contrast “PROD”; Sandbox amber “SANDBOX”; Dev blue “DEV” (colors optional — clarity mandatory).
2. Confirm tokens in `sandbox` vs `prod` properties would differ for banner text.
3. Get a peer to identify environment from screenshot alone.

**Expected result:** Peer correctly identifies sandbox from banner.

### Task 6 — Change control note

1. Record: UI branding changes promote via SSB like XML (Lesson 101).
2. List owners: IAM UX / `helen.ross` + CAB for prod banner changes.
3. Explicitly forbid behavior-changing JS in `web/` without plugin review.
4. Commit only `web/` sources — not exploded `build/`.

**Expected result:** Change-control paragraph in binder.

### Task 7 — Message bundle localization note

1. If lab uses only `en_US`, still namespace keys with `MNB_`.
2. Document that prod may require legal-approved language for login warnings.
3. Export customized messages into `web/` or config-controlled properties for SSB.

**Expected result:** Localization/ownership note.

### Task 8 — SSB bake verification (when WAR rebuild available)

1. `./build.sh -Dtarget=sandbox clean war`
2. Deploy or refresh lab
3. Hard-refresh browser; confirm banner + message key
4. Screenshot “after”

**Expected result:** After screenshots matching banner standard — or documented deferral if rebuild blocked.

### Task 9 — Examiner question drill

*"How do operators know they are not in production?"*

Write the three-artifact answer: (1) before/after login screenshots with SANDBOX word visible, (2) token note showing prod would differ, (3) change-control paragraph forbidding look-alike banners.

**Expected result:** Written proof steps in the binder.

---

## Acceptance criteria

- [ ] Before/after screenshots
- [ ] Environment banner or documented equivalent cue
- [ ] One Meridian message key customized or staged
- [ ] CSS overlay plan with safety rule
- [ ] Peer environment-ID test passed
- [ ] Promotion path referenced to SSB
- [ ] Localization/ownership note written
- [ ] Examiner proof steps drafted

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Banner not showing | Cache / CDN / not baked | Hard refresh; restart app if baked resource |
| Message key ignored | Wrong bundle / typo | Match exact key; check locale |
| CSS breaks layout | Over-broad selectors | Scope under Meridian class/banner id |
| Prod/sandbox confusion | Same banner text | Tokenize per env immediately |
| Unauthorized UIConfig edit | Capability | Restrict to SystemAdministrator / designated |
| Banner only on QuickLink | Incomplete design | Fix login/global banner first |

---

## Training binder evidence

- Before/after login + home screenshots
- Message key name/value
- Banner standard (SANDBOX/DEV/PROD)
- CSS safety rule note
- Change-control note
- Peer ID test result
- Examiner proof steps

---

## Knowledge check

1. Why must sandbox not look like production?
2. Where do SSB UI overlays live?
3. When should you use a plugin snippet instead of `web/` JS?
4. Who owns prod branding changes?
5. What must custom CSS never hide?
6. Why is color-only env coding insufficient?

### Answers

1. Prevents wrong-environment administration and irreversible prod changes.
2. `web/` (baked into WAR).
3. Page-specific behavior with versioning, rights, and install XML — governed extensions.
4. IAM lead with CAB; not ad-hoc operator taste.
5. Approval/certification controls or required legal/decision text.
6. Accessibility and clarity — word labels (`SANDBOX`/`PROD`) are mandatory.

---

## Further reading

- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search “UIConfig,” “branding,” and “message catalog” for version-specific surfaces.
- [docs/SSD.md](../SSD.md) — where `web/` overlays bake into the WAR.
- [W3C WCAG 2.2 Overview](https://www.w3.org/WAI/standards-guidelines/wcag/) — contrast and text resize expectations for banners and login text.
- [OWASP Cheat Sheet — Third Party JavaScript](https://cheatsheetseries.owasp.org/cheatsheets/Third_Party_Javascript_Management_Cheat_Sheet.html) — supply-chain mindset for CDN/script additions.
- [NIST SP 800-53 Rev. 5 — CM-2 / AC-8](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final) — baseline configuration and system use notification (login banners).

---

## Stretch lab

Draft `web/` overlay mock for Meridian favicon + login subtitle “Authorized users only — activity audited.” Confirm QuickLink branding is *not* treated as a substitute for the global banner.

---

## Summary

- Branding is an operational safety control for multi-env Meridian — not cosmetics.
- Prefer tokens + SSB overlays; gate behavior changes as plugins.
- Prove env identity with screenshots, peer checks, and word-labeled banners.

---

**Previous:** [Lesson 102 — Custom Java Services](102-custom-java-services.md)  
**Next:** [Lesson 104 — AuditConfig & SIEM](104-auditconfig-and-siem.md)
