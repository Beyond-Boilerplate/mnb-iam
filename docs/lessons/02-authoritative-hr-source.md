# Lesson 02 — Authoritative HR Source

**Level:** Beginner  
**Prereq:** Lesson 01  
**Meridian story:** HR is the system of truth for who works at the bank. You connect `HRApplications.txt` as Meridian’s authoritative application.

---

## Story

When a teller is hired in Kathmandu or a relationship manager joins in New York, HR gets the record first. IdentityIQ should learn about people from HR—not from random IT spreadsheets.

You will create application **`MNB-HR`** using the **Delimited File** connector pointed at `HRApplications.txt`.

---

## How it works

An **authoritative application** is trusted for identity attributes (name, email, manager, status, department).

Flow:

```text
HR file → Aggregation task → Account objects on MNB-HR
                          → (with create identities) Identity cubes
```

Important ideas:

- **Schema** = columns IIQ understands (`email`, `managerId`, …)
- **Aggregation** = read the file into IIQ
- **Authoritative** = this app may create/update identities

---

## Lesson goals

- [ ] Create Delimited File application `MNB-HR`
- [ ] Map schema attributes from `HRApplications.txt`
- [ ] Mark it as authoritative / able to create identities
- [ ] Run an aggregation successfully
- [ ] See HR people appear as identities (or accounts ready to become identities)

---

## Tasks

### Task 1 — Inspect the file

Confirm header line:

```text
employeeId,userName,firstName,lastName,gender,email,managerId,status,departmentCode,positionCode,jobCode,country,onLeave
```

Note delimiter is comma. Some rows have `status=0` (treat as inactive later) and `onLeave=true`.

### Task 2 — Create the application

1. Go to **Applications → Add New Application** (or equivalent).  
2. Name: `MNB-HR`.  
3. Owner: `spadmin` (lab fine).  
4. Connector: **DelimitedFile** (sometimes shown as Delimited File).  
5. File path: absolute path to your copy, e.g. `/Users/<you>/iiq-lab-data/HRApplications.txt`.  
6. Set delimiter `,`, set has header / parse header as appropriate for the UI.  
7. Save.

### Task 3 — Discover / define schema

1. Open `MNB-HR` → **Schema**.  
2. Discover schema from file if the button exists; otherwise add attributes manually to match headers.  
3. Identify a unique account attribute—use `employeeId` or `userName` as account identity attribute.  
4. Map “interesting” identity attributes: `email`, `firstname`/`firstName`, `lastname`/`lastName`, `manager`, department fields, `status`.

**Tip:** IIQ often prefers normalized names (`firstname`, `email`). You can map file columns to IIQ attribute names in the schema/UI.

### Task 4 — Authoritative settings

In application configuration / aggregation settings (wording varies):

1. Enable creating identities from this application (authoritative).  
2. Choose correlation basics if prompted—email or `userName` is fine for now (Lesson 05 goes deeper).  
3. Save.

### Task 5 — Create & run aggregation task

1. Create task **Account Aggregation** named `Aggregate MNB-HR`.  
2. Select application `MNB-HR`.  
3. Run now.  
4. Open task result—expect success with account counts > 0.

### Task 6 — Verify

1. Search identities for `manish.shrestha` or email `mshrestha@gmail.com`.  
2. Open the cube; confirm HR account exists.  
3. Spot-check a terminated/inactive user (`status=0`) and note how it looks today (you may refine inactive behavior in Lesson 07).

---

## Tips & tricks

- Always use an **absolute path** for delimited files on Tomcat; relative paths fail mysteriously.  
- If aggregation reads 0 accounts: header parsing, wrong path, or file permissions for the OS user running Tomcat.  
- After schema changes, re-run aggregation.  
- Keep names prefixed with `MNB-` so lab objects are obvious.

---

## Checkpoint

1. What makes an application “authoritative”?  
2. Why is `employeeId` a good account identifier?  
3. Where do you look if aggregation fails?

---

## Stretch

- Add a second HR file with one new hire; re-aggregate; confirm the new identity appears.  
- Document which HR fields should drive birthright roles later (department/job codes).

**Next:** [Lesson 03 — Build identity cubes](03-identity-cubes-and-refresh.md)
