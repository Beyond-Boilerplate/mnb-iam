# Enterprise lesson asserts

Machine-checkable PASS/FAIL proofs for Sandbox Path lessons **201+**.

```bash
./tools/lab/enterprise/verify-lesson.sh 203
./tools/lab/enterprise/verify-lesson.sh 201 202 203
./tools/lab/enterprise/verify-lesson.sh --all
```

Each line looks like:

```text
PASS  203.smtp-host  assert: SystemConfiguration defaultEmailHost == mailpit  [defaultEmailHost=mailpit]
FAIL  203.smtp-port  assert: SystemConfiguration defaultEmailPort == 1025  [defaultEmailPort expected '1025' got '']
```

`FAIL*` = soft check (reported, does not fail the lesson exit code).

## Academy "Verify now" wiring

The Academy site (`learn/build.py`) auto-enables the live **Verify now** button
for any 201–255 lesson that has a JSON spec here (`data-verify-mode="enterprise"`).
Lessons in that range with **no** spec fall back to `paperwork` (binder-complete
only). `tools/academy/serve.py`'s `POST /api/verify/<NNN>` routes 201–255 to
`verify_enterprise_lesson.py <NNN> --json` (stdout is a single JSON report;
progress lines go to stderr) and reshapes the result to match the classic
`mnb-lesson-verify-report/v1` schema the frontend expects. Add a spec here to
light up a new lesson's button — no Academy code changes needed.

## 203 — SMTP without UI Test Email

Notification Settings are stored on `Configuration` **SystemConfiguration**:

| UI field | Attribute |
| --- | --- |
| Email Notification Type | `emailNotifierType` (`smtp`) |
| Default SMTP Host | `defaultEmailHost` (`mailpit`) |
| Default SMTP Port | `defaultEmailPort` (`1025`) |
| Default From Address | `defaultEmailFromAddress` |

The verifier reads them via plugin REST / MCP export / iiq console fallback — same values the Notification Settings tab writes.

After configuring SMTP, send proof then re-verify:

```bash
./tools/lab/scripts/send-test-email.sh
./tools/lab/enterprise/verify-lesson.sh 203
```

## Specs

JSON under this directory. Add checks with `"assert": "..."` describing what is being tested.
