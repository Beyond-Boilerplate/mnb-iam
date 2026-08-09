# Lesson 242 — Customize an LCM Workflow

**Track:** Enterprise Sandbox Path (production-like local estate)  
**Time:** ~85 minutes  
**Prereq:** Lessons 217, 222  
**Stack:** `./tools/lab/docker/up.sh --enterprise`

**Maps to classic track:** 93

> **Why:** Stock LCM rarely matches bank approvals. A joiner process with no human checkpoint means birthright access can provision before anyone with authority confirmed the hire is real.

## What this is

`MNB-Workflow-Joiner` (`type="IdentityLifecycle"`) ships as the Lesson 217 minimum:

```text
Start → Log Joiner → Refresh (provision=true) → Stop
```

There is **no** manager gate and **no** pending-approval mail. You will insert both, rewire transitions so the gate is real (not decorative), hire disposable **`lab.wftest`**, and prove the case **pauses** until the manager completes the work item.

Nothing for this customization is pre-built. You will:

1. Verify-or-create `MNB-Workflow-Joiner` + `MNB-IdentityTrigger-Joiner` (Lesson 217 objects)  
2. Add **Notify Manager** + **Manager Approval** with exact designer or Debug Import steps  
3. Rewire `Log Joiner` → Notify → Approval → Refresh (not straight to Refresh)  
4. Hire `lab.wftest`, set manager `sanjay.kapoor`, fire the trigger  
5. Prove pause + Mailpit + post-approval Refresh  
6. Export the modified workflow  

## Know these

```text
Verify MNB-Workflow-Joiner (Log → Refresh) + IdentityTrigger
  → Customize:
       Log Joiner → Notify Manager → Manager Approval → Refresh → Stop
  → Create EmailTemplate (pending approval)
  → Hire lab.wftest + set Manager=sanjay.kapoor
  → Aggregate Workday + Refresh with Process events
  → Monitor → Workflows: case PAUSED at Manager Approval
  → Mailpit pending-approval mail
  → Sanjay completes work item
  → Refresh runs; case completes
```

| Step | Purpose |
| --- | --- |
| `Log Joiner` | Existing script log (`MNB Joiner workflow for …`) |
| `Notify Manager` (new) | EmailTemplate → Mailpit that approval is waiting |
| `Manager Approval` (new) | Work item owned by `identity.manager` |
| `Refresh` | Existing `refreshIdentity` — **only after** approval |
| `Transition` rewire | What makes the gate real vs a parallel no-op |

| Term | Plain English |
| --- | --- |
| **`explicitTransitions="true"`** | Steps advance only via `<Transition to="…">` |
| **Approval step** | Workflow pause until owner decides |
| **Work item** | What Sanjay sees under My Work Items |
| **Create trigger** | Fires once on cube create — new username required |

- **Wrong way:** Adding an Approval step without rewiring `Log Joiner`’s transition — case still jumps to Refresh.  
- **Wrong way:** Owner = `ref:launcher` or bare `identity.getManager()` without loading from `identityName` (Lesson 222 gotcha).  
- **Wrong way:** Expecting an old cube to re-fire Create — use `lab.wftest` (new).  
- **Wrong way:** Using Helen / Priya as the joiner subject.  
- **Wrong way:** Hand-waving “open the designer and add approval” without Import or click-level steps.

## Intent

- Customize `MNB-Workflow-Joiner` with Notify + Manager Approval using Option A (Import) or Option B (Business Processes).  
- Prove a live joiner case **pauses** before Refresh.  
- Prove Mailpit carries the pending-approval notice.  
- Complete the work item as the manager and confirm Refresh runs afterward.  
- Export the modified workflow XML.

## Before you start

Complete every checkbox. Do not skip into Task 1 until these are true.

- [ ] IIQ up as `spadmin` / `admin`
- [ ] Mailpit: [http://localhost:8025](http://localhost:8025)
- [ ] Lesson 217 concepts: joiner workflow + IdentityTrigger + Process events
- [ ] Manager identity you can log in as (or act for): **`sanjay.kapoor`** (password per lab seed / `LabUser1!` if that is your convention — confirm before Task 10)
- [ ] HCM healthy: `curl -sf http://localhost:8091/health`
- [ ] Evidence dir:

```bash
mkdir -p ~/iiq-lab-evidence/sandbox/242
```

## Do this

### Task 1 — Verify-or-create baseline joiner objects

Do **not** assume Lesson 217 objects survived a wipe.

1. **Debug** → Object Browser → type **`Workflow`** → search `MNB-Workflow-Joiner`  
   - Or **Setup → Business Processes** → same name  
2. If **missing**: Debug → **Import** paste from `config/Workflow/MNB-Workflow-Joiner.xml` (Lesson 217 Option A)  
3. Confirm steps today are **`Log Joiner` → `Refresh`** (pre-customization baseline)  
4. Debug → **`IdentityTrigger`** → `MNB-IdentityTrigger-Joiner`  
   - If missing: Import `config/IdentityTrigger/MNB-IdentityTrigger-Joiner.xml`  
   - Confirm workflow name is exactly **`MNB-Workflow-Joiner`** (not `MNB-Joiner-Workflow`)  
   - Not disabled  

- **Why:** customizing a missing workflow cannot work; trigger-before-workflow also fails.  
- **Expect:** both objects present before you edit.

### Task 2 — Create the pending-approval EmailTemplate

1. **Setup → Email Templates → Add New Email Template**  
2. Set:

| Field | Value |
| --- | --- |
| **Name** | `MNB-EmailTemplate-Joiner-Manager-Approval` |
| **Subject** | `Action required: approve joiner $identityName` |
| **Body** | `A new hire ($identityName) is waiting on Manager Approval before birthright provisioning. Open My Work Items in IdentityIQ.` |

3. **Save**

- **Why:** Notify step looks up this exact name.  
- **Expect:** template listed.

### Task 3 — Customize the workflow (pick Option A or B)

#### Option A — Debug Import (preferred, exact XML)

1. Open a text editor. Start from `config/Workflow/MNB-Workflow-Joiner.xml` and **replace the whole file contents** with the workflow below (or Import only into IIQ without touching git until you are happy).  
2. **Debug → Import** → paste → **Import**  
3. Re-open **Setup → Business Processes → MNB-Workflow-Joiner** and confirm the step order in Task 4’s table.

```xml
<?xml version='1.0' encoding='UTF-8'?>
<!DOCTYPE Workflow PUBLIC "sailpoint.dtd" "sailpoint.dtd">
<Workflow explicitTransitions="true" name="MNB-Workflow-Joiner" type="IdentityLifecycle">
  <Description>Enterprise Lab joiner with manager approval gate before birthright refresh.</Description>
  <Variable initializer="true" name="transient"/>
  <Variable input="true" name="identityName"/>
  <Variable input="true" name="identity"/>
  <Step icon="Start" name="Start" posX="20" posY="20">
    <Transition to="Log Joiner"/>
  </Step>
  <Step icon="Default" name="Log Joiner" posX="140" posY="20">
    <Script>
      <Source><![CDATA[
        import org.apache.commons.logging.LogFactory;
        LogFactory.getLog("meridian.lcm").warn("MNB Joiner workflow for " + identityName);
      ]]></Source>
    </Script>
    <Transition to="Notify Manager"/>
  </Step>
  <Step icon="Default" name="Notify Manager" posX="300" posY="20">
    <Script>
      <Source><![CDATA[
        import sailpoint.object.EmailOptions;
        import sailpoint.object.EmailTemplate;
        import sailpoint.object.Identity;
        import java.util.HashMap;
        import java.util.Map;

        Identity id = identity;
        if (id == null) {
          id = context.getObjectByName(Identity.class, identityName);
        }
        Identity mgr = (id != null) ? id.getManager() : null;
        String to = null;
        if (mgr != null && mgr.getEmail() != null) {
          to = mgr.getEmail();
        }
        if (to == null) {
          to = "sanjay.kapoor@meridiannb.com";
        }

        String tplName = "MNB-EmailTemplate-Joiner-Manager-Approval";
        EmailTemplate template = context.getObjectByName(EmailTemplate.class, tplName);
        if (template == null) {
          log.warn("MNB Joiner Notify: missing EmailTemplate " + tplName);
        } else {
          template = (EmailTemplate) template.deepCopy(context);
          Map args = new HashMap();
          args.put("identityName", identityName);
          EmailOptions ops = new EmailOptions(to, args);
          context.sendEmailNotification(template, ops);
          log.warn("MNB Joiner Notify: mailed " + to + " for " + identityName);
        }
      ]]></Source>
    </Script>
    <Transition to="Manager Approval"/>
  </Step>
  <Step icon="Approval" name="Manager Approval" posX="480" posY="20">
    <Approval mode="serial" owner="script:&#10;      import sailpoint.object.Identity;&#10;      Identity id = context.getObjectByName(Identity.class, identityName);&#10;      return (id != null) ? id.getManager() : null;&#10;    " renderer="lcmApprovalRenderer">
      <Arg name="workItemDescription" value="string:Confirm birthright access for $(identityName)"/>
    </Approval>
    <Transition to="Refresh"/>
  </Step>
  <Step action="call:refreshIdentity" icon="Task" name="Refresh" posX="660" posY="20">
    <Arg name="identity" value="ref:identityName"/>
    <Arg name="promoteAttributes" value="true"/>
    <Arg name="provision" value="true"/>
    <Arg name="correlateEntitlements" value="true"/>
    <Transition to="Stop"/>
  </Step>
  <Step icon="Stop" name="Stop" posX="820" posY="20"/>
</Workflow>
```

- **Why:** Import gives you exact transitions; no drag-drop mistakes.  
- **Expect:** Business Processes shows four work steps before Stop.

#### Option B — Business Processes designer (click-level)

Use this if you prefer the UI over Import. **Save after each major edit.**

1. **Setup → Business Processes → MNB-Workflow-Joiner** → open designer  
2. Select step **`Log Joiner`**  
   - Change its transition **from** `Refresh` **to** a new step name you will create: `Notify Manager`  
3. **Add Step** → name **`Notify Manager`**  
   - Kind: **Script**  
   - Paste the same BeanShell as in Option A’s `Notify Manager` `<Source>` (the email block)  
   - Transition **to** `Manager Approval`  
4. **Add Step** → name **`Manager Approval`**  
   - Kind: **Approval**  
   - Mode: **serial**  
   - **Owner** → **Script** → paste **exactly** (same Lesson 222 pattern):

```java
import sailpoint.object.Identity;
Identity id = context.getObjectByName(Identity.class, identityName);
return (id != null) ? id.getManager() : null;
```

   - Work item description: `Confirm birthright access for $(identityName)` (or UI equivalent)  
   - Transition **to** `Refresh`  
5. Confirm **`Refresh`** still has:

| Arg | Value |
| --- | --- |
| `identity` | `ref:identityName` |
| `promoteAttributes` | `true` |
| `provision` | `true` |
| `correlateEntitlements` | `true` |

   - Transition **to** `Stop`  
6. Confirm **no** transition still points `Log Joiner` → `Refresh`  
7. **Save** the business process  

- **Why:** the rewire is the whole lesson — decorative Approval steps fool designers and auditors.  
- **Expect:** step order matches Task 4.

> **Watch out:** Error `getManager() on undefined variable … identity` means you used `identity` in the Approval owner script. Load from `identityName` as above.

### Task 4 — Confirm the gate shape

Re-open the process and verify:

| Step | Transition to |
| --- | --- |
| Start | Log Joiner |
| Log Joiner | **Notify Manager** (not Refresh) |
| Notify Manager | Manager Approval |
| Manager Approval | Refresh |
| Refresh | Stop |

- **Expect:** table matches exactly. Screenshot under evidence as `workflow-steps.png`.

### Task 5 — Create disposable joiner `lab.wftest`

```bash
./tools/lab/enterprise/hcm-scenario.sh joiner lab.wftest WF Test \
  lab.wftest@meridiannb.com 'Bank Operations'
```

```bash
curl -s http://localhost:8091/hcm/v1/workers/lab.wftest \
  | python3 -m json.tool | grep -E 'userName|email|active|department'
```

1. Aggregate **`MNB-Workday`** → Complete  
2. **Do not** Refresh with Process events yet — set manager first (Task 6)

- **Why:** Create trigger fires on cube create during Refresh with Process events; manager must exist first or Approval has no owner.  
- **Expect:** worker in HCM; cube may appear after agg depending on your Refresh habits — if the cube already exists **without** a workflow case, continue (Task 8 fallback covers missed auto-fire).

### Task 6 — Set Manager before the trigger

1. **Identities → Identity Warehouse → `lab.wftest`**  
   - If missing: **Refresh Identity Cube** for `lab.wftest` **without** Process events first (create cube only)  
2. Edit identity → **Manager** = **`sanjay.kapoor`** (exact identity name)  
3. Set **email** on Sanjay if empty (`sanjay.kapoor@meridiannb.com`) so Notify can address him  
4. **Save** → re-open → confirm Manager  

- **Why:** Approval owner script returns `getManager()`; null manager = stuck or empty inbox.  
- **Expect:** manager = `sanjay.kapoor`.

### Task 7 — Fire the joiner path (Process events)

1. **Setup → Tasks → Refresh Identity Cube**  
2. Filter / include `lab.wftest` if possible  
3. Enable **Process events** (`processTriggers=true`)  
4. Enable promote / provision as you normally would for joiner  
5. **Save** → **Run Now** → Complete  

- **Why:** Create IdentityTriggers do not fire on aggregation alone.  
- **Expect:** `MNB-Workflow-Joiner` case starts for `lab.wftest`.

```bash
docker logs mnb-identityiq 2>&1 | grep -i "MNB Joiner workflow for lab.wftest" | tail -5
```

### Task 8 — Manual launch fallback (if Create already happened)

If the cube existed before Task 7 and no case appeared:

1. **Setup → Business Processes → MNB-Workflow-Joiner** → **Process** / **Launch** / **Run**  
2. `identityName` = `lab.wftest`  
3. Start the case  

- **Expect:** workflow case visible in Monitor (Task 9). Treat missed auto-fire as a finding, not a blocker.

### Task 9 — Prove the case is paused at Manager Approval

1. **Monitor → Processes → Workflows** (or Work Items / Identity Requests — use Workflows first)  
2. Find the case for `lab.wftest` / `MNB-Workflow-Joiner`  
3. Open detail  

- **Expect:** current step / state is **`Manager Approval`** (waiting), **not** already past **`Refresh`** / completed.  
- **Expect:** a work item exists: description like `Confirm birthright access for lab.wftest`, owner **Sanjay Kapoor**.

Screenshot as `~/iiq-lab-evidence/sandbox/242/paused-approval.png`.

> **Watch out:** If the case already completed Refresh with no Approval, your transition rewire did not save — return to Task 3/4.

### Task 10 — Prove Mailpit notification

1. Open [http://localhost:8025](http://localhost:8025)  
2. Find mail for Sanjay / subject containing **`lab.wftest`** or **approve joiner**  

- **Expect:** pending-approval message from Task 2’s template.  
- If missing: check Notify step logs (`MNB Joiner Notify`), Sanjay email on cube, Lesson 203 SMTP (`mailpit:1025`). Record an honest gap only if SMTP works but template tokens are blank — still require the work item pause proof.

Save screenshot or note under evidence.

### Task 11 — Complete approval as the manager

1. Log in as **`sanjay.kapoor`** (or use spadmin **Work Item** → forward/complete only if your lab blocks Sanjay login — note which path you used)  
2. **My Work Items** → open `Confirm birthright access for lab.wftest`  
3. **Approve** / Complete with a short comment: `Lab 242 manager OK`  
4. Return to **Monitor → Workflows**  

- **Expect:** case advances to **`Refresh`**, then **Complete** / Stop.  
- **Expect:** birthright provisioning side effects may continue (LDAP forms, etc. per Lesson 217) — the proof for *this* lesson is **Refresh did not run before approval**.

### Task 12 — Export the modified workflow

1. Debug → Workflow → `MNB-Workflow-Joiner` → copy XML  
2. Strip `id` / `created` / `modified`  
3. Save over (or beside) `config/Workflow/MNB-Workflow-Joiner.xml` per `config/README.md` when you are ready to promote  
4. Keep paused + Mailpit + post-approve screenshots in `~/iiq-lab-evidence/sandbox/242/`  

- **Expect:** re-importable workflow with Notify + Manager Approval intact.

Write the evidence note:

```text
lab.wftest
WorkflowCase: ________
Paused at: Manager Approval
Mailpit: yes / gap note
Approved by: sanjay.kapoor at ________
Refresh after approval: yes
```

## If it fails

| Symptom | Fix |
| --- | --- |
| Case skips Approval / completes immediately | `Log Joiner` still transitions to `Refresh` — redo Task 3/4 |
| Approval has no owner | Task 6 — Manager must be `sanjay.kapoor` before launch; resubmit / relaunch |
| Work item never appears | Confirm Approval step type + owner script; check Monitor → Work Items |
| No workflow case at all | Process events off; trigger disabled; wrong workflow name; use Task 8 launch |
| Mailpit empty | Notify script + template name; Sanjay email; SMTP Lesson 203 |
| `identity` undefined in owner script | Use `context.getObjectByName(Identity.class, identityName)` |
| Re-import schema errors | Validate transitions; Approval block well-formed; `explicitTransitions="true"` |
| Used shared persona as joiner | Stop — recreate with `lab.wftest` |

## You are done when

- [ ] `MNB-Workflow-Joiner` includes Notify Manager + Manager Approval (you added them)  
- [ ] Transitions gate Refresh behind Approval  
- [ ] Live case for `lab.wftest` **paused** at Manager Approval  
- [ ] Mailpit (or documented SMTP/template gap) checked  
- [ ] Manager completion advances case through Refresh  
- [ ] Exported workflow + evidence pack under `~/iiq-lab-evidence/sandbox/242/`  

## Control note

- **Control:** Human checkpoint before birthright provisioning (joiner process)  
- **Owner:** IAM Engineering + HR/Manager population  
- **SLA (lab):** Provisioning refresh held until approval work item completes  
- **Evidence:** `~/iiq-lab-evidence/sandbox/242/` + `config/Workflow/MNB-Workflow-Joiner.xml`  

## Quick check

1. What makes Approval a real gate vs decorative? → Transition rewire so Refresh is after Approval  
2. How does Approval resolve its owner? → Script loads Identity by `identityName`, returns `getManager()`  
3. Where do you confirm the case is paused? → Monitor → Processes → Workflows  
4. Why a new username (`lab.wftest`)? → Create triggers do not re-fire on existing cubes  
5. Which EmailTemplate name does Notify use? → `MNB-EmailTemplate-Joiner-Manager-Approval`  

## Feedback

Could you add Notify + Manager Approval to `MNB-Workflow-Joiner` with either Debug Import or designer clicks and prove a paused case without this page?

If something failed, note the **task number**, current workflow step name, whether Manager was set, and whether Process events was enabled.

## Navigate

- Previous: [Lesson 241](241-rules-before-after-live.md)
- Next: [Lesson 243](243-forms-live.md)
- Catalog: [_CATALOG_201_250.md](_CATALOG_201_250.md) · Coverage: [_COVERAGE_01_110.md](_COVERAGE_01_110.md) · Guide: [ENTERPRISE-LAB-V2.md](../ENTERPRISE-LAB-V2.md)
