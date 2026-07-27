# Meridian HR feed — real-bank column map

`lab-data/HRApplications.txt` uses a **production-style bank HRIS extract header** (52 columns). Governance lessons still talk about “department,” “manager,” “leaver,” and “leave”—those concepts map onto these fields.

## Native identity & correlation

| Governance concept | Bank column | Meridian lab value |
| --- | --- | --- |
| Account / cube key | `userId` | `MNB00001` … (same values formerly called employeeId) |
| Login-style name | `name` | `helen.ross` |
| Display | `displayName` / `fullName` | `Helen Ross` |
| Email | `email` | `@meridiannb.com` or vendor domain |
| Manager link | `managersAssociateID` → manager’s `userId` | e.g. `MNB00005` |
| Manager display | `manager` | `Rachel Evans` |

IT dumps (`EmployeeData.txt`) still carry `employeeId` — that value **equals** HR `userId` for correlation.

## Lifecycle signals

| Governance concept | Bank column(s) | Lab convention |
| --- | --- | --- |
| Active worker | `inactive=false`, `status=Active`, `statusFlag=A` | Most personas |
| Terminated (leaver) | `inactive=true`, `status=Terminated`, `statusFlag=T`, `terminationDate` set | `samir.hassan`, leaver drills |
| Leave of absence | `exceptions=LOA`, still `inactive=false` / `Active` | `sofia.torres` |
| Contractor | `employeeType` / `userType` = `Contractor`; optional `contractEndDate`, `rfSponser` | `raj.external` |
| Hire | `hireDate` | ISO date |

**Do not** treat `exceptions=LOA` as terminated. **Do not** drive leaver controls from `title` alone.

## Org / role drivers

| Governance concept | Bank column | Notes |
| --- | --- | --- |
| Department / population | `departmentName`, `division`, `SupORG` | Prefer codes in `JobCode` / `costCenter` for rules when stable |
| Job | `JobCode`, `title`, `corporateTitle` | Rule on `JobCode`, not free-text title |
| Location | `location`, `city`, `state`, `postalCode`, `rfLocationName` | `location` keeps lab codes (`US-NY`, …) |
| Cost center | `costCenter`, `costCenterName` | |
| Manager flag | `isManager` | `true` when someone appears as another row’s `managersAssociateID` |

## Full header (authoritative order)

```text
addressWork,city,company,companyNumber,contractEndDate,corporateTitle,costCenter,costCenterName,departmentName,desc,displayName,distinguishedName,division,domain,email,employeeType,exceptions,expirationDate,fax,firstname,fullName,hireDate,inactive,isManager,JobCode,lastname,location,locationTypeDesc,manager,managersAssociateID,managerStatus,middleName,mobilePhone,name,postalCode,previousJobTitle,projectID,rfFinancialManagerID,rfLocationName,rfSponser,RfSupervisoryOrganizationWID,state,status,statusFlag,SupORG,telephoneNumber,terminationDate,title,type,userId,userType,wid_owner
```

## Promote-to-identity minimum (Lesson 05)

Promote at least: `email`, `firstname`, `lastname`, `displayName`, `managersAssociateID` (→ manager), `departmentName` or `division`, `JobCode`, `inactive`, `status`, `employeeType` / `userType`, `exceptions`, `location`, `costCenter`, `hireDate`, `terminationDate`.

Scenario deltas under `lab-data/scenarios/**` use the **same header**.
