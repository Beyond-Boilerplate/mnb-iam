# Meridian National Bank — Lab Data

Realistic delimited files for the IdentityIQ 50-lesson curriculum.

## Quick copy

```bash
mkdir -p ~/iiq-lab-data
cp lab-data/HRApplications.txt lab-data/EmployeeData.txt ~/iiq-lab-data/
cp -R lab-data/apps lab-data/scenarios lab-data/reference ~/iiq-lab-data/
```

## Files

| Path | Purpose |
| --- | --- |
| `HRApplications.txt` / `hr/MNB-HR-Employees.csv` | Authoritative HR (~70 workers) |
| `EmployeeData.txt` / `apps/MNB-IT-Access.csv` | Consolidated entitlement dump |
| `apps/MNB-*.csv` | Per-platform extracts (Core, SAP, AWS, Wire, AD, …) |
| `reference/*` | Dept, job, entitlement, SoD dictionaries |
| `scenarios/*` | Joiner / mover / leaver delta rows |
| `notifications/certification-sample.txt` | Manager cert email tone |

Corporate email domain: `@meridiannb.com`

Scripted personas (use in lessons): `MNB00090`–`MNB00097`.
