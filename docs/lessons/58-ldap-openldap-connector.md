# Lesson 58 — LDAP / OpenLDAP Connector

**Level:** Intermediate  
**Track:** Connectors — Directory  
**Time:** 90–120 min  
**Prereq:** Lesson 57 — AD Groups, OUs & Exchange; connector matrix OpenLDAP row  

**Lab data:**
- Repo: `lab-data/connectors/ldap/mnb-openldap.ldif` + `README.md` (connection sheet)
- Live OpenLDAP is part of `./tools/lab/docker/up.sh` (service `openldap`). Standalone: `docker compose -f docker-compose.connectors.yml up -d openldap`

---

## Learning objectives

You will be able to:

- Explain LDAP as a protocol (versus Active Directory as a product) and read a Directory Information Tree, DN, and objectClass without guessing
- Start Meridian's live OpenLDAP container, verify it with `ldapsearch`, and predict aggregation results from the bootstrap LDIF before IIQ ever connects
- Create and configure **MNB-OpenLDAP** against the live directory: bind DN, base DN, account objectClass `inetOrgPerson`, and group entitlements from `groupOfUniqueNames`
- Run a real Test Connection and a real Account Aggregation, and reconcile the counts against the LDIF line by line
- Correlate LDAP accounts to HR identity cubes using `employeeNumber` with create-identities off
- Diagnose the four classic LDAP failures: `err=49`, `err=32`, connection refused, and size limit exceeded

---

## Why this matters

**Business.** Not every directory at Meridian is Active Directory. The wire-operations platform the bank bought in 2014 ships with an embedded OpenLDAP instance for its own authentication; the network team's switches and VPN concentrators authenticate against another one. When `priya.wire` was moved off wire duties last quarter, her AD group was removed on day one — but her entry in the wire platform's LDAP group `wire-initiators` sat untouched for five weeks, because nobody governs directories they cannot see. That is exactly the access an examiner will find, because embedded directories are where revocations go to die.

**Control / audit.** The control story is simple to state and easy to fail: *every directory that grants access is aggregated into IdentityIQ, correlated to an HR-owned identity, and its groups appear as certifiable entitlements.* An engineer who only knows AD Direct will mis-map `sAMAccountName` onto a directory that uses `uid`, break correlation, and quietly produce a fleet of uncorrelated accounts that no certification ever reaches. This lesson teaches the generic LDAP mental model so you can govern any RFC-compliant directory, not just Microsoft's.

---

## Concepts

### LDAP is a protocol; Active Directory is a product

LDAP (Lightweight Directory Access Protocol) is a wire protocol — a standardized way to search, read, and modify a tree-shaped database of entries. Active Directory is one *product* that speaks LDAP, alongside a pile of Microsoft-specific extensions (Kerberos, SIDs, `sAMAccountName`, `userAccountControl` bit flags). OpenLDAP is another product that speaks the same protocol but stays close to the standard schemas.

| | Active Directory | OpenLDAP |
| --- | --- | --- |
| Vendor | Microsoft, part of Windows Server | Open source, runs anywhere |
| Account objectClass | `user` (Microsoft schema) | `inetOrgPerson` (RFC 2798 standard) |
| Login attribute | `sAMAccountName` / `userPrincipalName` | `uid` |
| Enable/disable | `userAccountControl` bit flags | No standard flag — often `pwdAccountLockedTime` or app-specific |
| Group objectClass | `group` | `groupOfUniqueNames` (OOTB OpenLDAP - Direct; lab LDIF matches) |
| Group member attr | `member` | `uniqueMember` |
| Typical role at Meridian | Corporate workstation/app directory | Embedded app directories, network gear auth |

The practical consequence: when you sit down in front of an unfamiliar directory, your first questions are always *what objectClass are the accounts?* and *what attribute is the login name?* — never assumptions carried over from AD.

### The DIT, DNs, and RDNs

An LDAP directory is a tree called the **Directory Information Tree (DIT)**. Every entry has a **Distinguished Name (DN)** — its full address in the tree, written leaf-first. The leftmost component is the **Relative Distinguished Name (RDN)**, the entry's name within its parent container.

Meridian's lab DIT (abbreviated — full seed in `mnb-openldap.ldif`):

```
dc=meridiannb,dc=com                         ← suffix (the tree root)
├── ou=people,…                              ← inetOrgPerson accounts (10)
│   ├── uid=helen.ross … uid=priya.wire …
│   ├── uid=raj.external (contractor)
│   └── uid=samir.hassan (Inactive / leaver)
├── ou=groups,…                              ← groupOfUniqueNames entitlements (8)
│   ├── cn=wire-initiators, cn=wire-approvers
│   ├── cn=vpn-network-admins, cn=app-ldap-admins
│   └── cn=dept-*, cn=all-employees
└── ou=service,…                             ← reserved; read bind is cn=svc-iiq-read at suffix
```

Read `uid=priya.wire,ou=people,dc=meridiannb,dc=com` right to left: in the `meridiannb.com` tree, inside the `people` organizational unit, the entry whose RDN is `uid=priya.wire`. Unlike AD, where OUs mostly organize policy, in a plain LDAP directory the OUs are just containers — but you still need to know them, because they become your search bases.

### Bind DN and objectClass

A **bind DN** is the account IIQ authenticates *as* when it connects — LDAP's version of a service account. The lab uses the directory administrator, `cn=admin,dc=meridiannb,dc=com`, because osixia's image creates it automatically. Production never does this; see the hardening notes below.

An **objectClass** declares what kind of entry something is and which attributes it may carry. Three matter here:

- **`inetOrgPerson`** — the standard "person" class. Carries `uid`, `cn`, `sn`, `mail`, `employeeNumber`. This is Meridian's account objectClass.
- **`groupOfUniqueNames`** — members listed as full DNs in the `uniqueMember` attribute. This is what the lab LDIF uses (matches OOTB OpenLDAP - Direct group schema).
- **`groupOfNames`** — near-identical sibling that uses `member` instead of `uniqueMember`. If aggregation returns groups with zero members, the wrong member attribute name is the first suspect.

### Search base, scope, and filter

Every LDAP query has three coordinates, and the connector configuration is really just these three plus credentials:

- **Search base** — where in the tree to start, e.g. `ou=people,dc=meridiannb,dc=com`. Too narrow and you miss accounts; a typo and you get `err=32 No such object`.
- **Scope** — how deep to go: `base` (that one entry), `one` (immediate children), `sub` (entire subtree — the aggregation default).
- **Filter** — which entries qualify, e.g. `(objectClass=inetOrgPerson)`. This is why the objectClass decision matters: filter on `(objectClass=user)` out of AD habit and you aggregate zero accounts from OpenLDAP, with no error to tip you off.

Real-life check: when Priya's wire platform directory returns 0 accounts to a new engineer, the cause is almost never connectivity — it is one of these three coordinates being wrong, silently.

### Why banks still run OpenLDAP

It is tempting to treat OpenLDAP as legacy trivia. It is not, for two reasons that show up in every bank:

1. **App-embedded directories.** Vendor platforms (wire systems, trading tools, mainframe front-ends) frequently ship their own LDAP instance for local authentication and roles. The vendor will not migrate it to AD for you. If it grants access, you govern it.
2. **Network infrastructure auth.** Switches, routers, VPN concentrators, and out-of-band consoles commonly authenticate admins against a RADIUS/LDAP stack that is deliberately kept separate from the corporate domain — a blast-radius decision. Those admin groups are among the most sensitive entitlements in the bank.

---

## How it works

The SailPoint OpenLDAP / LDAP connector is one of the simplest in the catalog because there is no API gateway, token exchange, or agent: IIQ opens a TCP connection to the directory, binds, and issues standard LDAP search operations. Everything you configured in the concepts above maps one-to-one onto connector fields.

```
IdentityIQ (MNB-OpenLDAP application)
        │  bind: cn=admin,dc=meridiannb,dc=com  (lab)
        │        cn=svc-iiq-read,...            (production, read-only)
        ▼
LDAP simple bind over TCP 389 (lab) / LDAPS 636 (production)
        │
        ▼
OpenLDAP (osixia container, suffix dc=meridiannb,dc=com)
        ├── search base ou=people,  filter (objectClass=inetOrgPerson)
        │        → account aggregation (10 entries in the lab)
        ├── search base ou=groups,  filter (objectClass=groupOfUniqueNames)
        │        → group / entitlement aggregation (8 groups); use group.searchDNs
        └── uniqueMember DNs on groups → membership resolution back to accounts
```

| Operation | LDAP behavior | IIQ behavior |
| --- | --- | --- |
| Test Connection | Anonymous or simple bind as the bind DN | Proves host, port, credentials, and base DN in one click |
| Account aggregation | Subtree search under the people base, filtered by account objectClass | One Link per entry; `uid` as native identity |
| Group aggregation | Subtree search under the groups base, filtered by group objectClass | One ManagedAttribute per group |
| Membership resolution | Reads `member` (or `uniqueMember`) DNs on each group | Multi-valued entitlement attribute on each account |
| Provisioning (if enabled) | LDAP add/modify/delete operations | Create, attribute sync, group add/remove |

Note what is *absent* compared to AD Direct: no IQService, no Exchange, no forest topology. The trade is that OpenLDAP also has no standard "disabled" flag, so leaver evidence usually means *removed from groups and/or entry deleted*, and your runbook must say which.

---

## Real-world setup (outside IIQ)

Per the style contract, this lesson's live path is mandatory — the repo ships a real OpenLDAP backend, so you will configure against a directory that actually answers.

### Step 1 — Start the container

From the repo root:

```bash
# Preferred: main Meridian stack (includes OpenLDAP)
./tools/lab/docker/up.sh

# Or OpenLDAP alone
docker compose -f docker-compose.connectors.yml up -d openldap
docker compose -f docker-compose.connectors.yml ps
```

The `osixia/openldap:1.5.0` image reads its environment (`LDAP_DOMAIN: meridiannb.com`, `LDAP_ADMIN_PASSWORD: admin`) and builds the suffix `dc=meridiannb,dc=com` with admin `cn=admin,dc=meridiannb,dc=com` on first start. It then loads the mounted bootstrap file `lab-data/connectors/ldap/mnb-openldap.ldif`. Port 389 is mapped to localhost. From the IIQ container, use host **`openldap`**, not `localhost`.

One osixia quirk worth knowing now: **bootstrap LDIF is applied only on first container creation.** If you edit the LDIF later, recreate and wipe the OpenLDAP volumes (see `tools/lab/docker/README.md`).

### Step 2 — Verify with ldapsearch before touching IIQ

A production engineer never lets the connector be the first client to test a directory — a command-line bind isolates network and credential problems from connector configuration problems.

```bash
ldapsearch -x -H ldap://localhost:389 \
  -b dc=meridiannb,dc=com \
  -D cn=admin,dc=meridiannb,dc=com -w admin
```

Flag by flag: `-x` simple bind (no SASL), `-H` the directory URL, `-b` search base, `-D` bind DN, `-w` bind password. Expect the suffix, three OUs (`people`, `groups`, `service`), ten `inetOrgPerson` entries, two service binds, and eight `groupOfUniqueNames` — see `lab-data/connectors/ldap/README.md` for the inventory.

### Step 3 — Read the LDIF and predict the aggregation

Open `lab-data/connectors/ldap/mnb-openldap.ldif` and account for every entry. This is the discipline that makes aggregation results *verifiable* rather than merely *plausible*:

- Ten people keyed by `uid` / `employeeNumber` (e.g. `helen.ross` / `MNB00001`, `priya.wire` / `MNB00090`)
- Eight groups including `wire-initiators` (Priya, Michael Ross, Noah Ibrahim) and `wire-approvers` (Rachel Evans, Sanjay Kapoor)
- `samir.hassan` present but `description: Inactive` and **not** in any group (leaver drill)
- `raj.external` contractor in `dept-technology` only
- Service binds under `ou=service` (not aggregated as accounts if you filter `inetOrgPerson`)

So before running anything, write the prediction: **account aggregation scans 10 accounts; group aggregation finds 8 groups; `priya.wire` carries `wire-initiators` + `dept-treasury` + `all-employees`.** Any other numbers mean the configuration is wrong, no matter how green the task result looks.

### Production notes (what changes outside the lab)

- **Dedicated service binds.** Prefer `cn=svc-iiq-provision,ou=service,dc=meridiannb,dc=com` / `Provision1!` as the IIQ application bind when PROVISIONING is enabled (OpenLDAP connector uses **one** bind for aggregate + provision). Use `cn=svc-iiq-read,dc=meridiannb,dc=com` / `Readonly1!` only for aggregate-only labs. Never leave `cn=admin` in the app long-term.
- **LDAPS everywhere.** Simple binds send the password in cleartext. Production uses `ldaps://` on 636 (or StartTLS), which means the directory's certificate chain must live in the IIQ trust store — document who owns that trust store, because expired directory certs are a classic 2 a.m. outage.
- **Paged results.** Directories enforce a server-side size limit (OpenLDAP defaults to 500). A 40,000-entry directory will throw *size limit exceeded* mid-aggregation unless the connector requests the paged-results control. Two entries won't trigger it in the lab; forty thousand in production will, on your first full run.

---

## Before you start

- [ ] IIQ up at `http://localhost:8080/identityiq` as `spadmin`; `MNB-HR` identities exist (Lesson 06+) so correlation has targets
- [ ] OpenLDAP up (`./tools/lab/docker/up.sh` or `docker compose -f docker-compose.connectors.yml up -d openldap`)
- [ ] `ldapsearch` available (macOS ships it; Linux: `openldap-clients` / `ldap-utils` package)
- [ ] LDIF / connection sheet at `lab-data/connectors/ldap/`
- [ ] Lesson 52 connector selection record names **OpenLDAP - Direct** as preferred type

---

## Lab procedure

### Task 1 — Start and verify the live directory

Everything downstream depends on a directory that actually answers, so prove that first — exactly the order a production engineer follows when a new LDAP endpoint lands on their desk.

1. From the repo root, ensure OpenLDAP is up (`./tools/lab/docker/up.sh` or `docker compose -f docker-compose.connectors.yml up -d openldap`).
2. Run the Step 2 `ldapsearch` and count the entries returned.
3. Confirm you can name the shape: suffix, three OUs, ten people, two service binds, eight groups — including `wire-initiators` with Priya, Michael, and Noah as members.

**Expected result:** `ldapsearch` returns Success; `priya.wire`'s DN appears as a `uniqueMember` of `wire-initiators`.

**If it fails:** `Can't contact LDAP server` → container not running or port 389 not mapped (`docker compose ps`); `err=49` → bind DN/password typo (lab password is exactly `admin`).

### Task 2 — Predict the aggregation from the LDIF

Auditable aggregation starts with a written prediction — if you cannot say in advance what the task will return, you cannot detect when it returns the wrong thing.

1. Create `~/iiq-lab-data/connectors/ldap/MNB-OpenLDAP-schema-58.md` and record the prediction card: 10 accounts, 8 groups, Priya in `wire-initiators` (+ dept/all-employees).
2. Add the schema map:

| LDAP attribute | Schema use |
| --- | --- |
| `uid` | Account native identity |
| `cn`, `sn` | Display name / identity sync candidates |
| `mail` | Email; secondary correlation quality check |
| `employeeNumber` | Correlation to identity `userId` |
| `uniqueMember` on `groupOfUniqueNames` | Group membership → entitlement |

3. Record the correlation decision: primary `employeeNumber` ↔ `userId`; documented fallback `uid` ↔ `name`/`userName`. Create-identities: **No** — `MNB-HR` remains the only authoritative source.

**Expected result:** Prediction card and schema map saved before the application exists.

### Task 3 — Create the MNB-OpenLDAP application against the live container

Now consume the coordinates from concepts: host, port, bind DN, base DN. In production these come from the directory owner's handover sheet; here they come from the compose file.

1. Applications → Add New → **OpenLDAP - Direct** (or the generic **LDAP** type if Direct is absent from your build — document which you used, or equivalent menu path).
2. Name: `MNB-OpenLDAP`. Owner: `helen.ross` (lab session as `spadmin`).
3. Connection section:
   - **Host:** `openldap` if IIQ is in Docker; `localhost` if IIQ is on the host — **Port:** `389`
   - **Bind DN (user):** `cn=svc-iiq-provision,ou=service,dc=meridiannb,dc=com` — **Password:** `Provision1!` (annotate: *use this when PROVISIONING is on; aggregate-only labs may use `cn=svc-iiq-read` / `Readonly1!`*)
   - **Base / search DN:** `dc=meridiannb,dc=com`; if the form takes separate bases, people `ou=people,dc=meridiannb,dc=com` and groups `ou=groups,dc=meridiannb,dc=com`
   - **SSL/LDAPS:** off — label *lab only* in your notes
4. Save.

**Expected result:** Application saved with live connection values, not placeholders.

**If it fails:** If IIQ runs inside its own Docker network, `localhost` may need to be `host.docker.internal` (or the compose service name `openldap`) — the classic container-to-container networking trap.

### Task 4 — Test Connection

Test Connection is a real bind against a real directory here — it proves host, port, credentials, and base DN in a single click, which is why an examiner treats it as the first artifact of connector health.

1. Click **Test Connection** on `MNB-OpenLDAP`.
2. If it fails, reproduce with the Task 1 `ldapsearch` to split connector-config problems from directory problems.

**Expected result:** Success message. A failure here with a passing `ldapsearch` means the application fields differ from the working command — compare field by field.

**If it fails:** `err=49` → credential typo in the app; `err=32` → base DN typo (compare character-by-character with the LDIF suffix).

### Task 5 — Schema: account objectClass and group entitlements

The schema decides what governance can see; the objectClass filter decides what the schema even receives. This is where AD reflexes break non-AD directories.

1. Open the account schema. Confirm the account objectClass is `inetOrgPerson` (not `user`); native identity `uid`; attributes `cn`, `sn`, `mail`, `employeeNumber` present.
2. Open the group schema. Group objectClass `groupOfUniqueNames`, native identity `dn`, membership read from `uniqueMember`. Confirm **group.searchDNs** (objectType `group`) points at `ou=groups,…` — not a misnamed `groupOfNames.searchDNs` key. Mark group membership as the **entitlement attribute** so each group becomes a certifiable ManagedAttribute.
3. Correlation config: `employeeNumber` ↔ `userId` primary; `uid` ↔ `name`/`userName` fallback, both recorded in the schema file.
4. Confirm **create identities is OFF** — LDAP accounts that fail correlation must surface as uncorrelated accounts (Lesson 19 remediation), not spawn phantom cubes.

**Expected result:** Schema shows `inetOrgPerson` accounts keyed by `uid`, `groupOfUniqueNames` entitlements, create-identities disabled.

### Task 6 — Account Aggregation with predicted counts

Now run the inventory and hold it against your Task 2 prediction. A green task result with the wrong counts is a *worse* outcome than a red one, because nobody investigates green.

1. Tasks → New → Account Aggregation: `MNB-OpenLDAP-Account-Aggregation` (curriculum alias `Aggregate MNB-OpenLDAP`), application `MNB-OpenLDAP`.
2. Run it. Open the Task Result and record accounts scanned, created, updated.
3. Run group/entitlement aggregation per your build (separate Account Group Aggregation task or the connector's group scan).
4. Reconcile: **10 accounts scanned, 8 groups discovered.** Open `priya.wire`'s identity cube — the `MNB-OpenLDAP` link shows entitlement `wire-initiators` (plus dept/all-employees). Confirm `samir.hassan` correlates but has no group entitlements.
5. Confirm links correlated to their HR cubes via `employeeNumber` — no new identities created.
6. Schedule design note: nightly, after `MNB-HR` aggregation so correlation targets exist first.

**Expected result:** Task Result success with exactly 10 accounts; Priya's cube shows `wire-initiators`; zero identities created.

**If it fails:** 0 accounts → base DN or objectClass filter wrong (Task 5); group empty → `member` vs `uniqueMember` mapping; accounts uncorrelated → `employeeNumber` map or HR cubes missing.

### Task 7 — The governance payoff: wire-initiators as evidence

Connect the plumbing to the control story — this paragraph of narrative is what the examiner actually buys.

1. In the Entitlement Catalog, find `wire-initiators` on `MNB-OpenLDAP`. Set/describe it: *authorizes wire transfer initiation on the vendor wire platform*; flag as high-risk per Lesson 22 patterns.
2. Write the leaver expectation in the schema file: when Priya leaves wire operations, the provisioning plan (or the vendor admin, with an IIQ-verified deadline) removes her `uniqueMember` value; the next `Aggregate MNB-OpenLDAP` shows the entitlement gone — the before/after Task Results are the revocation evidence.
3. Note the OpenLDAP gap honestly: no standard disable flag, so "account disabled" is not an available control here — group removal and entry deletion are.

**Expected result:** Entitlement described and risk-flagged; leaver evidence chain written down, including the no-disable-flag caveat.

### Task 8 — Live provision stretch (group add → re-aggregate → remove)

Aggregation alone does not prove the write path. The main stack already applied ACLs for `cn=svc-iiq-provision,ou=service,dc=meridiannb,dc=com` / `Provision1!` — use that bind (not `cn=admin`) to change a group, then prove it in IIQ.

1. Switch `MNB-OpenLDAP` application bind to the **provision** service account (see [`lab-data/connectors/ldap/README.md`](../../lab-data/connectors/ldap/README.md)). Re-Test Connection.
2. Add teller `amelia.brooks` to `wire-initiators` via the provision bind:

```bash
ldapmodify -x -H ldap://localhost:389 \
  -D 'cn=svc-iiq-provision,ou=service,dc=meridiannb,dc=com' -w 'Provision1!' \
  -f lab-data/connectors/ldap/provision-stretch-add-wire.ldif
```

3. Confirm with a read bind:

```bash
ldapsearch -x -H ldap://localhost:389 \
  -b 'cn=wire-initiators,ou=groups,dc=meridiannb,dc=com' \
  -D 'cn=svc-iiq-read,dc=meridiannb,dc=com' -w 'Readonly1!' uniqueMember
```

4. Run **Account Aggregation** for `MNB-OpenLDAP`. Open `amelia.brooks` — she should now show `wire-initiators` (SoD-risky for a teller — binder finding).
5. Remove the membership (leaver / residual pattern) and re-aggregate:

```bash
ldapmodify -x -H ldap://localhost:389 \
  -D 'cn=svc-iiq-provision,ou=service,dc=meridiannb,dc=com' -w 'Provision1!' \
  -f lab-data/connectors/ldap/provision-stretch-remove-wire.ldif
```

6. Binder: before/after Task Results + note that OpenLDAP still has **no disable flag** — group remove is the evidence.

**Expected result:** Add and remove of `uniqueMember` proven via provision ACL + aggregation deltas for Amelia.

**If it fails:** `insufficient access` → ACL init did not run (`openldap-provision-acl`); wrong bind still on read-only `svc-iiq-read`. From IIQ container use host `openldap` not `localhost`.

Optional IIQ-native path: if your build can emit a Modify plan that adds/removes the group entitlement, execute one plan as stretch-on-stretch and still verify with `ldapsearch`.

### Task 9 — Production hardening notes

The lab deliberately violates three production rules; writing them down is what separates a lab exercise from training evidence.

1. In the schema file, record the three deltas from the Real-world setup section: (1) dedicated service bind (provision vs read) vaulted and rotated — not `cn=admin`; (2) LDAPS/StartTLS with named trust-store owner — plain LDAP requires an ADR exception; (3) paged results enabled before pointing at any directory larger than the server size limit.
2. Add the examiner line: *"Lab used plain LDAP on localhost; provision ACL + svc-iiq-provision exercised for group change; production design is documented at right."*

**Expected result:** Hardening section with all three deltas and the lab-only disclaimer.

### Task 10 — Fallback path (only if you cannot run Docker)

This path exists for locked-down machines; it is explicitly secondary and your binder must say the live path was unavailable, not skipped.

1. Complete Tasks 2, 3 (placeholder host `mnb-openldap:389`), 5, 7, and 9 using the LDIF as schema truth; skip Test Connection and mark Tasks 6 and 8 as *deferred — no live target*, keeping the prediction card as the expected-results record.

**Expected result:** All design artifacts complete; a dated deferred-aggregation note in the binder.

---

## Acceptance criteria

- [ ] OpenLDAP container running; `ldapsearch` returns Success with the seeded DIT
- [ ] Prediction card written *before* aggregation (10 accounts / 8 groups / Priya in wire-initiators)
- [ ] `MNB-OpenLDAP` created with live values; Test Connection passed
- [ ] Schema: `inetOrgPerson` accounts on `uid`, `groupOfUniqueNames` entitlements, create-identities off
- [ ] Aggregation Task Result matches the prediction exactly; accounts correlated by `employeeNumber`
- [ ] `wire-initiators` described and risk-flagged; leaver evidence chain written
- [ ] Provision stretch: Amelia added to / removed from `wire-initiators` via `svc-iiq-provision` + re-aggregate (or dated deferral)
- [ ] Hardening notes: service binds, LDAPS, paged results (fallback path: deferred note instead of live results)

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ldap_bind: Invalid credentials (49)` | Wrong bind DN or password | Lab bind is exactly `cn=admin,dc=meridiannb,dc=com` / `admin`; check for trailing spaces |
| `No such object (32)` | Base DN typo — e.g. `dc=meridianb,dc=com` | Compare the base DN character-by-character with the LDIF suffix |
| `Can't contact LDAP server` / connection refused | Container down, or port 389 not mapped to the host | `docker compose -f docker-compose.connectors.yml ps`; re-run `up -d openldap` |
| `Size limit exceeded (4)` mid-aggregation | Result set exceeds the server limit (OpenLDAP default 500) | Enable the paged-results control in the connector; never raise the server limit as the "fix" |
| Aggregation returns 0 accounts, task green | objectClass filter or people base wrong (AD habits) | Filter on `inetOrgPerson`, base `ou=people,dc=meridiannb,dc=com` |
| Group found but has no members | Directory uses `member` (`groupOfNames`), schema maps `uniqueMember` | Match the member attribute to the group objectClass actually in the directory |
| Zero groups aggregated | Search DN key is `groupOfNames.searchDNs` but schema objectType is `group` | Use `group.searchDNs` with `objectType=group` |

---

## Training binder evidence

- `ldapsearch` output showing Success and the seeded DIT
- Prediction card + `MNB-OpenLDAP-schema-58.md` with schema map and correlation decision
- Application screenshot (bind/base values visible, password masked) and Test Connection success
- Aggregation Task Result with counts reconciled against the prediction; Priya's cube showing `wire-initiators`
- Hardening notes with the lab-only disclaimer

**Examiner question:** *"This vendor wire platform doesn't use Active Directory. Show me how its accounts and the wire-initiation group get into your governance system, and how you'd prove a revocation."*

---

## Knowledge check

1. LDAP versus Active Directory — which is the protocol and which is the product, and why does the distinction change how you configure a connector?
2. Read `uid=priya.wire,ou=people,dc=meridiannb,dc=com` — what is the RDN, and what does the rest of the DN tell you?
3. Why does filtering on `(objectClass=user)` return zero accounts from this directory, with no error?
4. Why is binding as `cn=admin,dc=meridiannb,dc=com` acceptable in the lab but a finding in production?
5. What exact counts should `Aggregate MNB-OpenLDAP` report against the bootstrap LDIF, and why do you write them down *before* running?
6. OpenLDAP has no standard disable flag — what does that mean for your leaver evidence on this application?

### Answers

1. LDAP is the protocol; AD is one product speaking it (with Microsoft extensions). The connector must match the *product's* schema: `uid`/`inetOrgPerson` here, not `sAMAccountName`/`user`.
2. RDN is `uid=priya.wire` — her name within her container; the rest is the path: the `people` OU inside the `dc=meridiannb,dc=com` suffix.
3. The filter is a search predicate, not a validation — no entries carry `objectClass=user` in this directory, so the search legitimately matches nothing and succeeds with zero results.
4. Lab convenience on a disposable container. Production requires a dedicated read-only bind account with scoped ACLs, vaulted credentials, and rotation — admin binds violate least privilege and put a directory-admin password in connector config.
5. 10 accounts scanned, 8 groups (Priya in `wire-initiators` among others). Writing the prediction first turns the Task Result into verifiable evidence — a green task with wrong counts is otherwise invisible.
6. "Disabled" is not an available control; leaver evidence must be group removal (`member` gone on re-aggregation) and/or entry deletion, and the runbook must state which. (`samir.hassan` already models Inactive + no groups.)

---

## Further reading

- [OpenLDAP Software documentation](https://www.openldap.org/doc/) — the official admin guide; read the "Access Control" and "Limits" sections, which map directly to the read-only-bind and paged-results hardening notes.
- [ldap.com — Understanding LDAP DNs and RDNs](https://ldap.com/ldap-dns-and-rdns/) — the clearest standalone explanation of DN syntax; ten minutes here prevents a career of `err=32`.
- [ldap.com — LDAP filters](https://ldap.com/ldap-filters/) — filter syntax reference for the search-base/scope/filter triad, including the objectClass filters used in this lesson.
- [SailPoint IdentityIQ product documentation](https://documentation.sailpoint.com/) — search "OpenLDAP connector" or "LDAP connector" for the version-specific application guide, including paged-results and SSL settings.
- [SailPoint Developer Community](https://developer.sailpoint.com/discuss/) — search "OpenLDAP aggregation" for field-reported issues, especially `member` vs `uniqueMember` mapping threads.

---

## Stretch lab

Put `raj.external` into `wire-initiators` with the same provision-bind pattern (custom LDIF), re-aggregate, and document the contractor-in-wire-initiators finding for Lesson 40 policies. Optionally convert the container to LDAPS with a self-signed cert and document the trust-store import on the IIQ side.

---

## Summary

- LDAP is a protocol with a portable mental model — DIT, DN, bind DN, objectClass, and the base/scope/filter triad — that governs any directory, and AD habits (`sAMAccountName`, `user`) actively break non-AD directories.
- The live path is the lesson: a real container, a real `ldapsearch`, and an aggregation whose counts (10 accounts, 8 groups, Priya in `wire-initiators`) were predicted from the LDIF before the task ran.
- Production hardening is three deltas from the lab: dedicated read-only bind, LDAPS with an owned trust store, and paged results — plus the honesty note that OpenLDAP has no standard disable flag.

---

**Previous:** [Lesson 57 — AD Groups, OUs & Exchange](57-ad-groups-ous-exchange.md)  
**Next:** [Lesson 59 — Azure / Entra ID Connector](59-azure-entra-id-connector.md)
