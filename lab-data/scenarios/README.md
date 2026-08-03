# Meridian HR scenario packs

Deltas upsert into **`lab-data/HRApplications.txt`** by default (Docker mounts that path at `/opt/iiq-lab-data`). Override with `HR_FILE` for native Tomcat (`~/iiq-lab-data/HRApplications.txt`). Matching key: **`userId`**.

```bash
./tools/lab/scripts/scenarios/apply-joiner.sh
./tools/lab/scripts/scenarios/apply-mover.sh
./tools/lab/scripts/scenarios/apply-leaver.sh
./tools/lab/scripts/scenarios/apply-loa.sh
./tools/lab/scripts/scenarios/apply-rehire.sh
./tools/lab/scripts/scenarios/apply-batch-hire.sh
./tools/lab/scripts/scenarios/apply-contractor-end.sh

# Native Tomcat only:
# HR_FILE=~/iiq-lab-data/HRApplications.txt ./tools/lab/scripts/scenarios/apply-leaver.sh

# Diagnose-only (never upserts):
./tools/lab/scripts/scenarios/apply-bad-row.sh
./tools/lab/scripts/scenarios/apply-hr-delta.sh --diagnose lab-data/scenarios/bad-row/hr-delta-shifted-columns.csv
```

| Alias | Persona(s) | Lesson |
| --- | --- | --- |
| `joiner` | `nina.joiner` MNB00120 | 29 |
| `mover` | `priya.wire` MNB00090 | 30 |
| `leaver` | `jordan.reed` MNB00092 | 31 |
| `loa` / `on-leave` | `sofia.torres` MNB00095 | 33 |
| `rehire` | `samir.hassan` MNB00094 | 29b / stretch |
| `batch-hire` | `leo.batch` / `isla.batch` | 29 stretch / mid-34 |
| `contractor-end` | `raj.external` MNB00093 | 32 |
| `bad-row` | broken row (diagnose) | 08b / 19b |

Each successful apply writes `HRApplications.txt.bak-<timestamp>` beside the target file. Restore from that backup (or repo `lab-data/HRApplications.txt`) if a shared lab needs a clean slate.

Column map: [`../reference/hr-column-map.md`](../reference/hr-column-map.md).
