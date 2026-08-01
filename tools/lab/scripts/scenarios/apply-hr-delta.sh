#!/usr/bin/env bash
# Upsert HR delta rows into Meridian HRApplications.txt by userId.
# Usage:
#   ./tools/lab/scripts/scenarios/apply-hr-delta.sh joiner|mover|leaver|on-leave|loa
#   ./tools/lab/scripts/scenarios/apply-hr-delta.sh --file path/to/delta.csv
#   HR_FILE=~/iiq-lab-data/HRApplications.txt ./tools/lab/scripts/scenarios/apply-hr-delta.sh joiner
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
SCENARIOS="$ROOT/lab-data/scenarios"
REPO_HR="$ROOT/lab-data/HRApplications.txt"
HR_FILE="${HR_FILE:-$HOME/iiq-lab-data/HRApplications.txt}"

usage() {
  cat <<EOF
Usage: $(basename "$0") <joiner|mover|leaver|on-leave|loa>
       $(basename "$0") --file <delta.csv>

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
    *) return 1 ;;
  esac
}

DELTA=""
if [[ "${1:-}" == "--file" ]]; then
  DELTA="${2:-}"
  [[ -n "$DELTA" ]] || { usage; exit 2; }
elif [[ -n "${1:-}" ]]; then
  DELTA="$(resolve_delta "$1")" || { usage; exit 2; }
else
  usage
  exit 2
fi

if [[ ! -f "$DELTA" ]]; then
  echo "Delta not found: $DELTA" >&2
  exit 1
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

index = {r.get("userId", "").strip(): i for i, r in enumerate(hr_rows) if r.get("userId", "").strip()}
upserted = []
appended = []
for row in d_rows:
    uid = (row.get("userId") or "").strip()
    if not uid:
        raise SystemExit(f"Delta row missing userId: {row}")
    # Normalize to HR column order
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
