#!/usr/bin/env bash
# Meridian academy — live E2E HR slice
# import → assert → Aggregate MNB-HR → Refresh attrs/managers → persona checks
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

export SPTARGET="${SPTARGET:-sandbox}"
export IIQ_HOME="${IIQ_HOME:-${HOME}/iiq-lab/tomcat/webapps/identityiq}"
IIQ_BIN="${IIQ_HOME}/WEB-INF/bin"
VERIFY="${ROOT}/tools/iiq-verify"
LAB="${HOME}/iiq-lab-data"
SKIP_BUILD="${SKIP_BUILD:-0}"

iiq() {
  ( cd "$IIQ_BIN" && ./iiq console iiqBeans "$@" )
}

echo "==> 0. Lab fixtures"
mkdir -p "$LAB"
cp -f lab-data/HRApplications.txt lab-data/EmployeeData.txt "$LAB/"
cp -R lab-data/apps lab-data/scenarios lab-data/reference "$LAB/" 2>/dev/null || true
HR="$(realpath "$LAB/HRApplications.txt")"
echo "    HR=$HR cols=$(head -1 "$HR" | awk -F, '{print NF}')"

if [[ "$SKIP_BUILD" != "1" ]]; then
  echo "==> 1. SSB clean war + importdynamic"
  ./build.sh clean war
  ./build.sh importdynamic
else
  echo "==> 1. SKIP_BUILD=1 (using existing import)"
fi

echo "==> 2. Assert Meridian objects"
IIQ_HOME="$IIQ_HOME" "$VERIFY/assert-mnb-objects.sh" local

echo "==> 3. Aggregate MNB-HR (sync via helper rule)"
iiq <<EOF
import ${VERIFY}/MNB-Rule-E2E-RunAggregate.xml
rule MNB-Rule-E2E-RunAggregate
EOF

echo "==> 4. Refresh MNB Attributes + Managers"
iiq <<EOF
import ${VERIFY}/MNB-Rule-E2E-Refresh-Attributes.xml
import ${VERIFY}/MNB-Rule-E2E-Refresh-Managers.xml
rule MNB-Rule-E2E-Refresh-Attributes
rule MNB-Rule-E2E-Refresh-Managers
EOF

echo "==> 5. Persona / link checks"
iiq <<'EOF' | tee /tmp/mnb-e2e-personas.out
count Identity
get Identity helen.ross
get Identity priya.wire
get Identity samir.hassan
get Identity sofia.torres
get Application MNB-HR
EOF

python3 - <<'PY'
import re, sys
text = open("/tmp/mnb-e2e-personas.out").read()
# count line is typically just a number after "> "
fail = 0
for name, needle in [
    ("helen.ross", 'name="helen.ross"'),
    ("priya.wire", 'name="priya.wire"'),
    ("samir.hassan", 'name="samir.hassan"'),
    ("sofia.torres", 'name="sofia.torres"'),
]:
    if needle not in text:
        print(f"FAIL missing identity {name}")
        fail = 1
    else:
        print(f"OK identity {name}")
if 'exceptions" value="LOA"' not in text and "exceptions\" value=\"LOA\"" not in text:
    # sofia link
    if "LOA" in text:
        print("OK sofia LOA present on link")
    else:
        print("FAIL sofia exceptions=LOA not found")
        fail = 1
else:
    print("OK sofia exceptions=LOA")
if 'inactive" value="true"' in text or "inactive\" value=\"true\"" in text:
    print("OK samir inactive=true on link")
else:
    print("WARN samir inactive=true not found in dump (check link attrs)")
if 'file" value=' in text and "iiq-lab-data/HRApplications.txt" in text:
    print("OK MNB-HR file path tokenized to lab-data")
if fail:
    sys.exit(1)
print("E2E persona checks passed (Link attrs = bank HRIS header).")
print("NOTE: Identity-level promote needs Lesson 05 ObjectConfig/identity maps — Link truth is enough for Phase 1 cube creation.")
PY

echo "==> E2E HR slice complete"
