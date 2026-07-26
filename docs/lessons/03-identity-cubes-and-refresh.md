# Lesson 03 — Identity Cubes & Refresh

**Level:** Beginner  
**Prereq:** Lesson 02 (`MNB-HR` aggregated)  
**Meridian story:** HR accounts exist. Now you make sure IdentityIQ continuously recalculates each person’s cube so managers, status, and roles stay true.

---

## Story

A cube is not a static row. When HR changes a department code, or when AD groups arrive later, IIQ must **refresh** the identity: recompute attributes, manager links, role assignments, policy flags, and sometimes provisioning needs.

---

## How it works

Common pipeline:

```text
Aggregate apps → Identity Refresh → (optional) role changes / provisioning
```

**Identity Refresh** can:

- Promote account attributes onto the identity
- Resolve manager references (`managerId` → manager identity)
- Re-evaluate assigned / detected roles
- Check policies
- Refresh risk scores

You will run refresh after almost every major data change for the rest of this curriculum.

---

## Lesson goals

- [ ] Understand identity attributes vs account attributes
- [ ] Configure / run an **Identity Refresh** task for Meridian users
- [ ] Verify manager relationships on a few cubes
- [ ] Clean obvious test identities if needed

---

## Tasks

### Task 1 — Compare account vs identity

1. Open identity `manish.shrestha` (or similar).  
2. Find the `MNB-HR` account.  
3. Note which attributes live on the account vs on the identity header.

**Mental model:** Accounts are per-application; the identity is the merged person view.

### Task 2 — Manager linkage

From HR data, `a2` (`ravi.shah`) reports to `a1` (`manish.shrestha`).

1. Open `ravi.shah`.  
2. Check whether Manager is populated.  
3. If not, ensure `managerId` is mapped and that refresh options include manager correlation / hierarchy processing.  
4. Run refresh (Task 3) and re-check.

### Task 3 — Create Identity Refresh task

1. Tasks → New → **Identity Refresh** (name: `Refresh MNB Identities`).  
2. Filter to identities that have an account on `MNB-HR` if the UI allows; otherwise refresh all (lab size is small).  
3. Enable sensible options for a lab, typically along the lines of:
   - Refresh identity attributes  
   - Refresh manager links  
   - Refresh assigned / detected roles (ok if no roles yet)  
4. Run and open the task result.

### Task 4 — Spot-check a population

Pick three people:

| Person | Why |
| --- | --- |
| Top-level manager (empty `managerId`) | Should have no manager or org root behavior |
| Mid-level manager | Should show direct reports later |
| `status=0` user | Mark mentally as leaver candidate |

Record what looks correct vs incomplete in your notebook.

### Task 5 — Optional identity mapping tweak

If first/last name or email did not promote cleanly:

1. Adjust application attribute mappings / identity mappings.  
2. Re-aggregate `MNB-HR`.  
3. Re-run `Refresh MNB Identities`.

---

## Tips & tricks

- Aggregation without refresh = stale cubes. When demos “don’t update,” refresh was often skipped.  
- For large prod directories, refresh is scheduled and filtered; in lab, run on demand.  
- Manager correlation needs the manager identity to already exist—aggregate HR fully before judging manager links.  
- Use Global Settings / Identity mappings docs in product PDFs if attribute promotion is confusing.

---

## Checkpoint

1. What does Identity Refresh do that Aggregation does not?  
2. Why might a manager field be blank even though `managerId` is in the file?  
3. When should you re-run refresh in later lessons?

---

## Stretch

- Schedule `Refresh MNB Identities` daily at 2 AM (even on a laptop lab—practice the scheduling UI).  
- Create a population “MNB Active Employees” based on `status=1` if your attribute mapping supports it.

**Next:** [Lesson 04 — Onboard bank applications](04-onboard-bank-applications.md)
