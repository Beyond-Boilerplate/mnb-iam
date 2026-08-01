# Meridian National Bank — Lab Data

Realistic delimited files for the IdentityIQ curriculum.

## File paths for Delimited File apps (read this first)

IIQ reads the path **from the Tomcat process**, not from your Mac Finder.

| How you run IIQ | Path to put on the Application |
| --- | --- |
| **Docker lab** (`./tools/lab/docker/up.sh`) | `/opt/iiq-lab-data/HRApplications.txt` |
| Native / local Tomcat | Absolute host path, e.g. `/Users/you/iiq-lab-data/HRApplications.txt` (expand `~`; do not paste a Mac path into Docker IIQ) |

Repo `lab-data/` is bind-mounted into the IIQ container as **`/opt/iiq-lab-data`** (read-only). Same layout for `EmployeeData.txt`, `apps/`, `scenarios/`, etc.

```text
Host:   <repo>/lab-data/HRApplications.txt
Docker: /opt/iiq-lab-data/HRApplications.txt
```

If aggregation fails with `Unable to open filestream`, you almost certainly used a host `/Users/...` path against Docker IIQ.

## Quick copy (native Tomcat only)

```bash
mkdir -p ~/iiq-lab-data
cp lab-data/HRApplications.txt lab-data/EmployeeData.txt ~/iiq-lab-data/
cp -R lab-data/apps lab-data/scenarios lab-data/reference ~/iiq-lab-data/
```

Docker learners: skip the copy — edit files under repo `lab-data/`; IIQ already sees them at `/opt/iiq-lab-data/…`.

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
