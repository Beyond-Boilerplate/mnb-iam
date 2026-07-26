# Lesson 04 — Onboard Bank Applications

**Level:** Beginner → Intermediate  
**Prereq:** Lessons 02–03  
**Meridian story:** HR tells you who people are. Now connect the systems that hold *access*—starting with a consolidated IT access file, then splitting critical bank platforms.

---

## Story

MNB’s IT team gives you `EmployeeData.txt`: a pragmatic dump of who has which platform entitlement (`ODS`, `AWS`, `SAP`, …). It is messy (duplicate usernames appear on multiple rows)—exactly like real life.

You will:

1. Create **`MNB-IT-Access`** as a Delimited File application for the whole file.  
2. Model `itAccess` as an **entitlement** attribute.  
3. (Stretch) Split high-risk apps conceptually (`MNB-SAP`, `MNB-AWS`).

---

## How it works

Target applications usually contribute:

- **Accounts** (the user’s login on that system)
- **Entitlements** (groups/permissions)

For delimited files, one common pattern is:

- Account id = `userName` or `email`
- Entitlement attribute = multi-valued group column (`itAccess`)

Because the file has **one entitlement per row**, aggregation may create multiple rows per user. Connectors/schema options (merge / group by account) matter—expect to iterate.

---

## Lesson goals

- [ ] Create `MNB-IT-Access` application
- [ ] Define account + entitlement schema
- [ ] Aggregate successfully and see entitlements on accounts
- [ ] Document Meridian’s entitlement dictionary (table in lessons README)

---

## Tasks

### Task 1 — Profile the file

Header:

```text
userName,firstName,lastName,email,jobTitle,itAccess
```

Count how many distinct `userName` values vs rows. Notice duplicates like `gsmith` with multiple `itAccess` values—this is good (multi-entitlement user).

### Task 2 — Create `MNB-IT-Access`

1. New Delimited File application `MNB-IT-Access`.  
2. Point to `~/iiq-lab-data/EmployeeData.txt` (absolute path).  
3. Delimiter `,`, headers on.  
4. Save.

### Task 3 — Schema design

1. Account identity attribute: `userName` (or `email` if you prefer uniqueness).  
2. Mark `itAccess` as an **entitlement** / group attribute in schema.  
3. Include `email`, names, `jobTitle` as account attributes useful for correlation.  
4. Save.

### Task 4 — Aggregation

1. Task `Aggregate MNB-IT-Access`.  
2. Run.  
3. Inspect task result: accounts + entitlement counts.  
4. Open a multi-entitlement user (e.g. search identities/accounts related to `gsmith` or `mgomez`) and confirm multiple entitlements if correlation already links them—or inspect the application’s account list.

### Task 5 — Business glossary

In your notebook, copy the entitlement meaning table from [lessons/README.md](README.md) and add one risk rating each (`Low` / `Medium` / `High`). Example: `AWS` and `SAP` = High for a bank.

### Task 6 — Do **not** mark this app authoritative

Confirm `MNB-IT-Access` does **not** create identities. Only `MNB-HR` should. IT access apps correlate onto existing people.

---

## Tips & tricks

- If every row becomes a separate account for the same person, adjust schema/aggregation merging / entitlement configuration—this is a classic delimited-file learning moment.  
- Prefer correlating on `email` when usernames differ between HR and IT files.  
- Keep owners assigned (even `spadmin`)—certifications later need application/entitlement owners optionally.

---

## Checkpoint

1. Difference between authoritative HR app and target IT app?  
2. What is an entitlement in one sentence?  
3. Why are duplicate usernames with different `itAccess` values useful?

---

## Stretch

Create a second application `MNB-SAP-File` that is a filtered extract containing only `itAccess=SAP` rows (make a small CSV yourself). Aggregate it separately. This mirrors how banks often onboard one high-risk system at a time.

**Next:** [Lesson 05 — Account correlation mastery](05-account-correlation.md)
