#!/usr/bin/env bash
# Ensure compile classpath jars exist under build/extract/WEB-INF/lib.
#
# Order:
#   1) Already present from ./build.sh clean war
#   2) docker cp from a running IIQ container (Docker lab — no base/ga zip needed)
#   3) Fail with next-step hint
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LIB="$ROOT/build/extract/WEB-INF/lib"
CONTAINER="${IIQ_CONTAINER:-mnb-identityiq}"
# Paths inside the official Meridian IIQ image / stock layout
GUEST_LIB_CANDIDATES=(
  /usr/local/tomcat/webapps/identityiq/WEB-INF/lib
  /opt/iiq-stock/WEB-INF/lib
)

JARS=(
  identityiq.jar
  connector-bundle-identityiq.jar
  jakarta.ws.rs-api-2.1.6.jar
  log4j-1.2-api-2.17.1.jar
  log4j-api-2.17.1.jar
  slf4j-api-1.7.32.jar
  commons-logging-1.2.jar
)

need_stage=0
for j in "${JARS[@]}"; do
  if [[ ! -f "$LIB/$j" ]]; then
    need_stage=1
    break
  fi
done
if [[ "$need_stage" -eq 0 ]]; then
  echo "IIQ libs OK → $LIB"
  exit 0
fi

if ! docker inspect "$CONTAINER" >/dev/null 2>&1; then
  echo "ERROR: $LIB/identityiq.jar missing and container '$CONTAINER' is not running." >&2
  echo "  Fix: ./build.sh clean war   (needs base/ga/identityiq-8.5.zip)" >&2
  echo "    or: start the Docker lab so jars can be copied from $CONTAINER" >&2
  exit 1
fi

guest_lib=""
for cand in "${GUEST_LIB_CANDIDATES[@]}"; do
  if docker exec "$CONTAINER" test -f "$cand/identityiq.jar" 2>/dev/null; then
    guest_lib="$cand"
    break
  fi
done
if [[ -z "$guest_lib" ]]; then
  echo "ERROR: identityiq.jar not found inside $CONTAINER (checked ${GUEST_LIB_CANDIDATES[*]})." >&2
  exit 1
fi

mkdir -p "$LIB"
echo "Staging IIQ libs from ${CONTAINER}:${guest_lib} → $LIB"
missing=0
for j in "${JARS[@]}"; do
  if docker cp "${CONTAINER}:${guest_lib}/$j" "$LIB/$j" 2>/dev/null; then
    echo "  + $j"
  else
    echo "  ! missing in container: $j" >&2
    missing=1
  fi
done
if [[ ! -f "$LIB/identityiq.jar" ]]; then
  echo "ERROR: failed to copy identityiq.jar from $CONTAINER" >&2
  exit 1
fi
if [[ "$missing" -ne 0 ]]; then
  echo "WARN: some optional classpath jars were missing; compile may fail" >&2
fi
echo "Staged OK → $LIB"
