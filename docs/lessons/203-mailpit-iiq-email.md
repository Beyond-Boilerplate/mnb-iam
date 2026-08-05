# Lesson 203 — Catch All Mail in Mailpit

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~35 minutes  
**Prereq:** Lesson 201  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 49

> **Why (1–2 lines):** You cannot trust an approval, a certification, or a joiner workflow until you can actually read the email it claims to send. An examiner treats "the system says it emailed the certifier" as unproven until there's a captured message.

## What this is

Mailpit (`axllent/mailpit`) is a catch-all SMTP server with a web UI — nothing it receives ever leaves your machine. It replaces a real corporate mail relay for every lesson from here forward that touches notification email: manager certs (226), approvals (222), break-glass (223), and the various LCM workflows (217–219). IIQ talks to it over the **Docker network** as host `mailpit` port `1025` — that's different from the **host-published** SMTP port (`1026` by default; `1025` is often already taken by other local mail tools, which is exactly why the compose file remaps it). The UI is always at `http://localhost:8025/`. This is the one enterprise service every later lesson checks first when something "should have" sent mail but didn't visibly work.

## Know these

| Endpoint | Value | Used by |
| --- | --- | --- |
| Docker-internal SMTP | `mailpit:1025` | IIQ's own outbound mail config |
| Host-published SMTP | `localhost:1026` (`MAILPIT_SMTP_PORT`) | your host shell / manual test tools |
| Web UI | `http://localhost:8025/` | you, reading captured mail |

**Wrong way:** Pointing IIQ's Email Settings at `localhost:1025` — IIQ runs *inside* the `mnb-identityiq` container, and `localhost` there means the container itself, not your host or Mailpit.

## Intent

- Know the two different SMTP endpoints (Docker-internal `mailpit:1025` vs. host `localhost:1026`) and never confuse them.
- Configure IIQ's outbound email settings to point at Mailpit and prove it with a real test send.
- Read a message's raw source at least once so you know what a real SMTP payload looks like.
- Recognize the difference between "IIQ didn't send" and "IIQ sent but Mailpit didn't catch it."

## Before you start

- [ ] Lesson 201 stack up
- [ ] IIQ reachable at `http://localhost:8080/identityiq`, logged in as `spadmin`
- [ ] Mailpit UI loads at `http://localhost:8025/`
- [ ] Evidence dir: `mkdir -p ~/iiq-lab-evidence/sandbox/203`

## Do this

1. Open the Mailpit UI: `http://localhost:8025/`.  
   **Why:** this is your evidence locker for the rest of the path — know its empty state before you rely on it.  
   **Expect:** empty inbox, or leftover mail from a previous run.

2. In IIQ, go to **Gear icon → Global Settings → Email Settings** and set Host `mailpit`, Port `1025`, Encryption none/plaintext, From `iiq-noreply@meridiannb.com`.  
   **Why:** Mailpit accepts unauthenticated, unencrypted SMTP by design (`MP_SMTP_AUTH_ACCEPT_ANY`/`MP_SMTP_AUTH_ALLOW_INSECURE` in the compose file) — no credentials to configure.  
   **Expect:** settings save without validation error.

3. Confirm you understand *why* it's `mailpit` and not `localhost`: IIQ and Mailpit share the same Compose network, and Compose gives every service a DNS name equal to its service name.  
   **Why:** your browser reaches the UI at `localhost:8025` from outside Docker; IIQ reaches the SMTP port at `mailpit:1025` from inside it — two different vantage points, two different hostnames.  
   **Expect:** you can state this distinction from memory before moving on.

4. Send IIQ's built-in test email from the Email Settings page, then refresh `http://localhost:8025/`.  
   **Why:** this is the actual round-trip proof, not just a saved config.  
   **Expect:** a new message appears from `iiq-noreply@meridiannb.com` within a few seconds.

5. Open the message and click "View source" once.  
   **Why:** you're looking for a real `Date:`/`From:`/`To:`/`Message-ID:` header block — what a SOC or audit team would eventually see in a mail archive, not just a UI toast that says "sent."  
   **Expect:** a legible raw SMTP payload with standard headers.

6. Read `lab-data/enterprise/mail/README.md`.  
   **Why:** it documents the exact host/port pair and notes some IIQ images configure email via `iiq.properties` overlays instead of the UI — this path prefers the UI so the setting stays visible and repeatable.  
   **Expect:** README content matches what you just configured.

7. Optional: prove Mailpit itself is listening independent of IIQ from your host shell: `echo "Subject: manual test" | curl -sS --url "smtp://localhost:${MAILPIT_SMTP_PORT:-1026}" --mail-from test@meridiannb.com --mail-rcpt you@meridiannb.com --upload-file -`.  
   **Why:** isolates "Mailpit is broken" from "IIQ's config is wrong" if step 4 ever fails later.  
   **Expect:** requires a `curl` build with SMTP support; skip if unavailable — step 4 already proves the path you actually need.

8. Note which later lessons this exact configuration underwrites before moving on: manager certs (226), delegated/emergency access approvals (222–223), and every joiner/mover/leaver workflow (217–219) all assert their success partly by checking Mailpit.  
   **Why:** if any of those lessons later reports "no mail," the fix is almost always here, not in the workflow logic itself.  
   **Expect:** you can name at least two of those lesson numbers from memory.

## If it fails

- **Test email send errors immediately** — confirm host is exactly `mailpit` (not `localhost`/`127.0.0.1`) and port `1025` (not `1026`).
- **Send reports success but Mailpit UI stays empty** — refresh the page (no auto-poll); check `docker logs mnb-mailpit` for a rejected connection; confirm `mnb-mailpit` and `mnb-identityiq` share a Compose network.
- **Mailpit UI won't load at `:8025`** — container isn't healthy yet; give it the documented 10s `start_period`.
- **Later lessons' approval/cert mail never shows up** — re-verify Email Settings host/port here first before debugging the workflow — this is the most common false alarm in Lessons 217–232.

## You are done when

A test email sent from IIQ's Email Settings page appears in `http://localhost:8025/` with a legible raw source, and you can state from memory which SMTP endpoint (`mailpit:1025`) IIQ uses versus which one your host tools would use (`localhost:1026`).

## Control note

- **Control:** Notification delivery assurance — email is proven, not just configured.
- **Owner:** IAM Ops / Messaging.
- **SLA (lab):** verified before any downstream lesson (217–232) claims mail-based evidence.
- **Evidence:** `~/iiq-lab-evidence/sandbox/203/` — test mail screenshot, raw source view.

## Quick check

1. Which SMTP endpoint does IIQ itself use? → `mailpit:1025` (Docker-internal).
2. Which port would your host shell use instead? → `localhost:1026` (host-published).
3. What's the first thing to re-check when later mail "silently fails"? → Email Settings host/port here, before the workflow.

## Navigate

- Previous: Lesson 202
- Next: Lesson 204
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
