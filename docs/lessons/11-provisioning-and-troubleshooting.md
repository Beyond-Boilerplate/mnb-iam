# Lesson 11 — Provisioning & Troubleshooting

**Level:** Advanced beginner / Intermediate  
**Prereq:** Lessons 07–10  
**Meridian story:** Approvals and certifications only matter if access actually changes. You learn how provisioning plans work and how to debug when “nothing happened.”

---

## Story

IdentityIQ computes a **Provisioning Plan**: create/modify/disable accounts, add/remove entitlements. Connectors execute the plan—or create manual work items when the system cannot be written to (common with flat files).

You will inspect plans, task results, provisioning transactions, and logs.

---

## How it works

```text
Trigger (request, lifecycle, cert revoke, role change)
  → Plan compiled
  → (optional) Plan rules modify requests
  → Provisioner runs
  → Connector or manual action
  → Result stored / retries / failures surfaced
```

**Debug mindset for Meridian:**

1. Did the trigger fire?  
2. Was a plan created?  
3. Was it executed or filtered?  
4. Did the connector succeed?  
5. Did refresh show the new truth?

---

## Lesson goals

- [ ] Find provisioning transactions / request details for a prior approval or revoke
- [ ] Intentionally cause a failure and read the error
- [ ] Use `catalina.out` + IIQ task results together
- [ ] Know when to use `iiq console`

---

## Tasks

### Task 1 — Trace a known change

Use an access request from Lesson 08 or a cert revoke from Lesson 10.

1. Open the identity.  
2. Find Access Requests / Provisioning Activity / History (labels vary).  
3. Note plan operations: `Create`, `Modify`, `Disable`, `Remove`.

### Task 2 — Read task failures

1. Open **Tasks** → recent results with warnings/errors.  
2. Expand messages.  
3. Classify: config error, data error, connectivity, permission.

### Task 3 — Log correlation

1. Reproduce a small aggregation.  
2. Tail Tomcat logs:

```bash
tail -f "$CATALINA_HOME/logs/catalina.out"
```

3. Match timestamps between UI task result and log lines.

### Task 4 — Console skills

```bash
cd "$IIQ_HOME/WEB-INF/bin"
./iiq console
```

Try safe commands such as listing / counting (per your version’s help), and practice:

```text
help
quit
```

Use console `import` only for XML you trust.

### Task 5 — Manual provisioning path

If `MNB-IT-Access` cannot be written:

1. Find the manual work item generated for an approved change.  
2. Complete it as IT.  
3. Optionally update the CSV to mirror reality, then re-aggregate so IIQ matches the world.

**This dual bookkeeping is exactly why writable connectors matter in production.**

---

## Tips & tricks

- “Approved but not provisioned” is usually workflow end states, unanswered manual items, or connector misconfig—not magic.  
- Turn on temporary detailed logging carefully; turn it off after.  
- Never delete random objects in Debug to “fix” provisioning—export first.  
- Encrypt secrets with `./iiq encrypt` before paste into `iiq.properties` when you leave pure lab mode.

---

## Checkpoint

1. What is a provisioning plan?  
2. Why do delimited file apps often create manual work items?  
3. Name three places to look when access did not change.

---

## Stretch

Configure a JDBC or LDAP target (Docker LDAP is a popular lab upgrade) and perform a true create/add-group provision for a joiner.

**Next:** [Lesson 12 — Audit-ready reporting & ops](12-reporting-and-ops.md)
