#!/usr/bin/env bash
# Upsert HR delta rows into Meridian HRApplications.txt by userId.
# Usage:
#   ./tools/lab/scripts/scenarios/apply-hr-delta.sh <alias>
#   ./tools/lab/scripts/scenarios/apply-hr-delta.sh --file path/to/delta.csv
#   ./tools/lab/scripts/scenarios/apply-hr-delta.sh --diagnose path/to/delta.csv
#   HR_FILE=~/iiq-lab-data/HRApplications.txt ./tools/lab/scripts/scenarios/apply-hr-delta.sh joiner
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
SCENARIOS="$ROOT/lab-data/scenarios"
REPO_HR="$ROOT/lab-data/HRApplications.txt"
HR_FILE="${HR_FILE:-$HOME/iiq-lab-data/HRApplications.txt}"

usage() {
  cat <<EOF
Usage: $(basename "$0") <alias>
       $(basename "$0") --file <delta.csv>
       $(basename "$0") --diagnose <delta.csv>

Aliases:
  joiner          Nina Foster new hire (MNB00120)
  mover           Priya Mehta transfer to Commercial (MNB00090)
  leaver          Jordan Reed terminate (MNB00092)
  on-leave|loa    Sofia Torres exceptions=LOA (MNB00095)
  rehire          Samir Hassan rehire (MNB00094)
  batch-hire      Leo + Isla batch hire day (MNB00121/122)
  contractor-end  Raj external SOW end-date (MNB00093)
  bad-row         Diagnose-only — refuses to upsert

Upserts delta data rows into HR_FILE by matching the userId column.
Creates a timestamped .bak beside HR_FILE before writing.

Env:
  HR_FILE   Target HR feed (default: ~/iiq-lab-data/HRApplications.txt)
EOF
}

resolve_delta() {
  case "$1" in
    joiner) echo "$SCENARIOS/joiner/hr-delta-new-hire.csv" ;;
    mover) echo "$SCENARIOS/mover/hr-delta-priya-to-commercial.csv" ;;
    leaver) echo "$SCENARIOS/leaver/hr-delta-terminate-jordan.csv" ;;
    on-leave|loa) echo "$SCENARIOS/on-leave/hr-delta-sofia-loa.csv" ;;
    rehire) echo "$SCENARIOS/rehire/hr-delta-rehire-samir.csv" ;;
    batch-hire|batch) echo "$SCENARIOS/batch-hire/hr-delta-batch-hire-day.csv" ;;
    contractor-end|contractor) echo "$SCENARIOS/contractor-end/hr-delta-raj-contract-end.csv" ;;
    bad-row|bad) echo "$SCENARIOS/bad-row/hr-delta-bad-row-diagnose.csv" ;;
    *) return 1 ;;
  esac
}

MODE="apply"
DELTA=""
ALIAS=""

if [[ "${1:-}" == "--file" ]]; then
  DELTA="${2:-}"
  [[ -n "$DELTA" ]] || { usage; exit 2; }
elif [[ "${1:-}" == "--diagnose" ]]; then
  MODE="diagnose"
  DELTA="${2:-}"
  [[ -n "$DELTA" ]] || { usage; exit 2; }
elif [[ -n "${1:-}" ]]; then
  ALIAS="$1"
  DELTA="$(resolve_delta "$1")" || { usage; exit 2; }
  if [[ "$ALIAS" == "bad-row" || "$ALIAS" == "bad" ]]; then
    MODE="diagnose"
  fi
else
  usage
  exit 2
fi

if [[ ! -f "$DELTA" ]]; then
  echo "Delta not found: $DELTA" >&2
  exit 1
fi

diagnose_delta() {
  python3 - "$DELTA" "$REPO_HR" <<'PY'
import csv
import sys
from pathlib import Path

delta_path = Path(sys.argv[1])
hr_path = Path(sys.argv[2])

issues = []
with delta_path.open(newline="", encoding="utf-8") as f:
    sample = f.read()
lines = sample.splitlines()
if not lines:
    raise SystemExit("Empty delta file")

# Detect shifted/short rows before DictReader loses them
header = next(csv.reader([lines[0]]))
for i, line in enumerate(lines[1:], start=2):
    if not line.strip():
        continue
    cols = next(csv.reader([line]))
    if len(cols) != len(header):
        issues.append(f"line {i}: field count {len(cols)} != header {len(header)} (column shift risk)")

with delta_path.open(newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    d_header = list(reader.fieldnames or [])
    d_rows = list(reader)

with hr_path.open(newline="", encoding="utf-8") as f:
    hr_header = list(csv.DictReader(f).fieldnames or [])

if d_header != hr_header:
    missing = [c for c in hr_header if c not in d_header]
    extra = [c for c in d_header if c not in hr_header]
    if missing:
        issues.append(f"header missing columns: {missing}")
    if extra:
        issues.append(f"header extra columns: {extra}")

for idx, row in enumerate(d_rows, start=2):
    uid = (row.get("userId") or "").strip()
    if not uid:
        issues.append(f"row {idx}: blank userId — cannot upsert safely")
    inactive = (row.get("inactive") or "").strip().lower()
    status = (row.get("status") or "").strip()
    exceptions = (row.get("exceptions") or "").strip()
    if inactive in {"true", "1", "yes"} and status == "Active":
        issues.append(f"row {idx} ({uid or '?'}): inactive=true but status=Active (contradiction)")
    if exceptions == "LOA" and inactive in {"true", "1", "yes"}:
        issues.append(f"row {idx} ({uid or '?'}): exceptions=LOA with inactive=true (leave vs terminate confusion)")
    hire = (row.get("hireDate") or "").strip()
    if hire and (len(hire) < 8 or hire[0].isalpha()):
        issues.append(f"row {idx} ({uid or '?'}): suspicious hireDate={hire!r}")
    mgr = (row.get("managersAssociateID") or "").strip()
    if mgr.startswith("MNB") and mgr not in {r for r in []} and len(mgr) == 8:
        # soft note only — full HR scan optional
        pass
    if mgr == "MNB99999":
        issues.append(f"row {idx} ({uid or '?'}): managersAssociateID=MNB99999 (missing manager cube)")
    email = (row.get("email") or "").strip()
    if email == "helen.ross@meridiannb.com" and (row.get("name") or "") != "helen.ross":
        issues.append(f"row {idx} ({uid or '?'}): email collides with helen.ross")

print(f"Diagnose: {delta_path}")
print(f"  data rows: {len(d_rows)}")
if issues:
    print(f"  FINDINGS ({len(issues)}):")
    for issue in issues:
        print(f"   - {issue}")
    print("  Action: fix delta before apply-hr-delta.sh — do NOT upsert into live HR.")
    sys.exit(1)
print("  No structural issues found. Safe to apply with --file if intended.")
PY
}

if [[ "$MODE" == "diagnose" ]]; then
  diagnose_delta
  exit $?
fi

if [[ ! -f "$HR_FILE" ]]; then
  mkdir -p "$(dirname "$HR_FILE")"
  if [[ -f "$REPO_HR" ]]; then
    cp "$REPO_HR" "$HR_FILE"
    echo "Seeded $HR_FILE from repo HRApplications.txt"
  else
    echo "HR file missing and repo seed not found: $REPO_HR" >&2
    exit 1
  fi
fi

BAK="${HR_FILE}.bak-$(date +%Y%m%d-%H%M%S)"
cp "$HR_FILE" "$BAK"
echo "Backup: $BAK"

python3 - "$HR_FILE" "$DELTA" <<'PY'
import csv
import sys
from pathlib import Path

hr_path = Path(sys.argv[1])
delta_path = Path(sys.argv[2])

def read_rows(path: Path):
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise SystemExit(f"No header in {path}")
        rows = list(reader)
        return list(reader.fieldnames), rows

header, hr_rows = read_rows(hr_path)
d_header, d_rows = read_rows(delta_path)

if header != d_header:
    missing = [c for c in header if c not in d_header]
    extra = [c for c in d_header if c not in header]
    raise SystemExit(
        f"Header mismatch.\n  missing in delta: {missing}\n  extra in delta: {extra}"
    )

if "userId" not in header:
    raise SystemExit("HR feed must include userId column (see lab-data/reference/hr-column-map.md)")

for row in d_rows:
    if not (row.get("userId") or "").strip():
        raise SystemExit(
            "Delta contains blank userId — refuse upsert. "
            "Run: ./tools/lab/scripts/scenarios/apply-hr-delta.sh --diagnose <file>"
        )

index = {r.get("userId", "").strip(): i for i, r in enumerate(hr_rows) if r.get("userId", "").strip()}
upserted = []
appended = []
for row in d_rows:
    uid = (row.get("userId") or "").strip()
    normalized = {c: row.get(c, "") for c in header}
    if uid in index:
        hr_rows[index[uid]] = normalized
        upserted.append(uid)
    else:
        hr_rows.append(normalized)
        index[uid] = len(hr_rows) - 1
        appended.append(uid)

with hr_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    writer.writerows(hr_rows)

print(f"HR updated: {hr_path}")
print(f"  upserted ({len(upserted)}): {', '.join(upserted) or '—'}")
print(f"  appended ({len(appended)}): {', '.join(appended) or '—'}")
print("Next: Aggregate MNB-HR → Refresh MNB Attributes (and Managers/Roles as needed).")
PY
