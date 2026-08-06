# Lesson 203 — Catch All Mail in Mailpit

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~45 minutes  
**Prereq:** Lesson 201 (202 recommended)  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 49

> **Why:** You cannot trust an approval, a certification, or a joiner workflow until you can actually *read* the email it claims to send. “The system emailed the certifier” is unproven until there is a captured message.

## What this is

**Mailpit** (`axllent/mailpit`) is a catch-all SMTP server with a web UI. Nothing it receives ever leaves your machine. From this lesson forward, every notification-heavy lab (approvals 222, break-glass 223, manager certs 226, LCM 217–219) depends on this wiring.

Two ports matter — do not mix them up:

| Endpoint | Value | Used by |
| --- | --- | --- |
| Docker-internal SMTP | `mailpit:1025` | IIQ’s outbound mail config |
| Host-published SMTP | `localhost:1026` (`MAILPIT_SMTP_PORT`) | your host shell / manual probes |
| Web UI | http://localhost:8025/ | you, reading captured mail |

This build’s **Notification Settings** page usually has **no Test Email button**. You prove SMTP the way ops often does in the field:

1. Create a tiny **EmailTemplate**
2. Create a **BeanShell Rule** that calls `context.sendEmailNotification(...)`
3. Run the rule and watch Mailpit

## Know these

| Lab object | Name |
| --- | --- |
| EmailTemplate | `MNB-EmailTemplate-Lab-Test` |
| Rule | `MNB-Rule-Send-Test-Email` |
| To address | `lab-test@meridiannb.com` |
| Subject | `Meridian lab SMTP test` |

- **Wrong way:** Pointing IIQ’s Notification SMTP at `localhost:1025` — IIQ runs *inside* the `mnb-identityiq` container, and `localhost` there means the container itself, not your host or Mailpit.

> **Watch out:** `mailpit` (hostname) + port `1025` for IIQ. `localhost:1026` only for tools running on your Mac/Linux host.

## Intent

- Configure Notification Settings for Mailpit and assert host/port from outside the UI.
- **Create** an EmailTemplate and a send-test Rule yourself, then **run** the rule.
- Confirm the message in Mailpit (including raw source).
- Know that later cert/approval lessons depend on this SMTP wiring.

## Before you start

- [ ] Lesson 201 stack up
- [ ] IIQ at http://localhost:8080/identityiq, logged in as `spadmin`
- [ ] Mailpit UI loads at http://localhost:8025/
- [ ] Evidence dir ready:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/203
```

## Do this

### Task 1 — Open Mailpit

Know the empty (or leftover) inbox before you send anything — otherwise you can’t tell *your* test from an older message.

1. Open http://localhost:8025/

- **Why:** Mailpit is the evidence surface for every later mail-heavy lesson.
- **Expect:** Mailpit UI loads.

### Task 2 — Configure Notification Settings

This UI build usually has **no Test Email button** — you configure SMTP here, then prove delivery with a Rule.

1. In IIQ: **Gear → Global Settings → IdentityIQ Configuration → Notification Settings**
2. Set:

   | Setting | Value |
   | --- | --- |
   | Email Notification Type | **SMTP** (or SMTP / Basic) |
   | Default SMTP Host | `mailpit` |
   | Default SMTP Port | `1025` |
   | Encryption | **NONE** / plaintext |
   | Default From Address | `iiq-noreply@meridiannb.com` |

3. **Save**

- **Why:** IIQ must use the Docker-internal hostname — `localhost` inside the IIQ container is not Mailpit.
- **Expect:** settings save without error.

> **Watch out:** Host tools use `localhost:1026`. IIQ uses `mailpit:1025`. Mixing them is the #1 failure mode.

### Task 3 — Assert SMTP was saved

```bash
./tools/lab/enterprise/verify-lesson.sh 203
```

- **Why:** reads `SystemConfiguration` keys `defaultEmailHost`, `defaultEmailPort`, `emailNotifierType` outside the UI.
- **Expect:** hard asserts for host=`mailpit`, port=`1025`, notifier=SMTP show **PASS**. Soft checks for rule/Mailpit message may `FAIL*` until Tasks 4–7.

### Task 4 — Create the EmailTemplate

`sendEmailNotification` needs a template object — subject/body are what you will see in Mailpit.

1. **Setup → Email Templates** (or **Gear → Global Settings → Email Templates**)
2. **Add New Email Template**
3. Set:
   - **Name:** `MNB-EmailTemplate-Lab-Test`
   - **Subject:** `Meridian lab SMTP test`
   - **Body** (plain text is fine):

     ```text
     Mailpit round-trip OK.

     Sent by rule MNB-Rule-Send-Test-Email from the Meridian enterprise lab.
     ```

4. **Save**

- **Why:** exact name matters — the Rule looks up this template by name.
- **Expect:** template appears in the list as `MNB-EmailTemplate-Lab-Test`.

> **Tip:** Prefer UI craft. Debug import from `config/EmailTemplate/MNB-EmailTemplate-Lab-Test.xml` is only an alternate if you already know the form.

### Task 5 — Create the send-test Rule

This is the same API path workflows use for notifications — if it works, approvals/certs can mail later.

1. **Setup → Rules** (or **Gear → Global Settings → Rules**)
2. **Add New Rule**
3. Set:
   - **Name:** `MNB-Rule-Send-Test-Email`
   - **Type:** leave default / none required (not a connector rule)
   - **Language:** BeanShell
   - **Description:** `Lab SMTP proof for Mailpit`
4. Paste this **Source** (exact):

```java
import sailpoint.object.EmailOptions;
import sailpoint.object.EmailTemplate;
import java.util.HashMap;

String to = "lab-test@meridiannb.com";
String tplName = "MNB-EmailTemplate-Lab-Test";
EmailTemplate template = context.getObjectByName(EmailTemplate.class, tplName);
if (template == null) {
  return "FAIL missing EmailTemplate " + tplName;
}
template = (EmailTemplate) template.deepCopy(context);
EmailOptions ops = new EmailOptions(to, new HashMap());
context.sendEmailNotification(template, ops);
return "OK sent to " + to + " via " + tplName;
```

5. **Save**

- **Why:** BeanShell compile is checked when you run it — save first, then execute.
- **Expect:** rule saved under that exact name.

**Alternate:** Debug import `config/Rule/MNB-Rule-Send-Test-Email.xml`.

### Task 6 — Run the Rule

**Option A — Debug (recommended)**

1. Open **Debug** (`http://localhost:8080/identityiq/debug`)
2. Object type **Rule** → **`MNB-Rule-Send-Test-Email`**
3. **Run Rule** / execute
4. Confirm return value starts with `OK sent to lab-test@meridiannb.com`

**Option B — IIQ console (Docker)**

```bash
docker exec -it mnb-identityiq bash -lc \
  'cd /usr/local/tomcat/webapps/identityiq/WEB-INF/bin && ./iiq console'
```

At the `>` prompt:

```text
rule MNB-Rule-Send-Test-Email
```

- **Why:** a green save is not proof — the run is the send.
- **Expect:** `OK sent to lab-test@meridiannb.com via MNB-EmailTemplate-Lab-Test`.

### Task 7 — Confirm in Mailpit + re-verify

1. Refresh http://localhost:8025/
2. Open the message with subject **Meridian lab SMTP test** (To: `lab-test@meridiannb.com`)
3. Click **View source** — confirm `Date:` / `From:` / `To:` / `Message-ID:` headers
4. Re-run:

```bash
./tools/lab/enterprise/verify-lesson.sh 203
```

- **Why:** config + send + capture is the full ops proof — later cert/approval lessons assume this path works.
- **Expect:** message present with legible raw source; hard SMTP asserts PASS; soft Mailpit-subject / rule / template checks PASS (or no longer `FAIL*`).

Save a screenshot under `~/iiq-lab-evidence/sandbox/203/`.

### Task 8 — Optional shortcuts (not required)

Only if you already completed Tasks 4–6 by hand:

```bash
./tools/lab/scripts/send-test-email.sh
```

Host-only Mailpit probe (note the leading **`echo`** — host port `1026`, not IIQ’s `1025`):

```bash
echo "Subject: manual test" | curl -sS --url "smtp://localhost:${MAILPIT_SMTP_PORT:-1026}" \
  --mail-from test@meridiannb.com --mail-rcpt you@meridiannb.com --upload-file -
```

## If it fails

| Symptom | Fix |
| --- | --- |
| Rule returns `FAIL missing EmailTemplate` | Task 4 — create/save `MNB-EmailTemplate-Lab-Test` with that **exact** name |
| Rule / send errors immediately | Host must be `mailpit` (not `localhost`); port `1025`; notifier type SMTP — re-run `verify-lesson.sh 203` |
| Send OK but Mailpit empty | Refresh Mailpit; `docker logs mnb-mailpit`; confirm IIQ + Mailpit share the Compose network |
| BeanShell compile error | Re-paste the Source block; imports must be at the top |
| Debug has no Run Rule | Use Option B (iiq console) or optional `send-test-email.sh` |
| `verify-lesson.sh` can’t read SystemConfiguration | IIQ/MCP down — start stack; hard SMTP asserts need a live IIQ |

## You are done when

- [ ] You created **`MNB-EmailTemplate-Lab-Test`** and **`MNB-Rule-Send-Test-Email`** yourself
- [ ] You **ran** the rule and saw `OK sent to…`
- [ ] Mailpit shows **Meridian lab SMTP test** with raw headers
- [ ] `./tools/lab/enterprise/verify-lesson.sh 203` hard SMTP asserts are **PASS**

## Control note

- **Control:** Notification delivery assurance — email is proven, not just configured
- **Owner:** IAM Ops / Messaging
- **SLA (lab):** verified before any downstream lesson (217–232) claims mail-based evidence
- **Evidence:** `~/iiq-lab-evidence/sandbox/203/` — template/rule names, Mailpit screenshot, verify output

## Quick check

1. Which SMTP endpoint does IIQ itself use? → `mailpit:1025` (Docker-internal)
2. Which port would your host shell use instead? → `localhost:1026` (host-published)
3. Why build a Rule instead of clicking Test Email? → this UI build usually has no Test Email button; the rule uses the same send API as workflows
4. Which SystemConfiguration keys hold SMTP host/port? → `defaultEmailHost` / `defaultEmailPort`

## Feedback

Could you reconfigure SMTP and send a test message from memory? If mail never appeared, note **Task number**, whether the rule returned `OK`, and what Mailpit showed (empty vs wrong subject).

## Navigate

- Previous: [Lesson 202](202-identity-master-and-seed.md) · or [Lesson 207](207-hcm-workday-shaped.md) if you already created Workday cubes
- Next: [Lesson 204](204-openldap-live-ops.md) *(requires Lesson 207 cubes first)*
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md) · Mail notes: [mail/README.md](../../lab-data/enterprise/mail/README.md)
