#!/usr/bin/env bash
# Compile Meridian IAM Toolkit plugin classes against extracted IIQ WAR libs.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LIB="$ROOT/build/extract/WEB-INF/lib"
SRC="$ROOT/pluginsrc/mnb-iam-toolkit/src"
OUT="$ROOT/pluginsrc/mnb-iam-toolkit/build/classes"
if [[ ! -f "$LIB/identityiq.jar" ]]; then
  echo "ERROR: $LIB/identityiq.jar missing — run ./build.sh clean war first" >&2
  exit 1
fi
rm -rf "$OUT"
mkdir -p "$OUT"
CP="$LIB/identityiq.jar:$LIB/connector-bundle-identityiq.jar:$LIB/jakarta.ws.rs-api-2.1.6.jar:$LIB/log4j-1.2-api-2.17.1.jar:$LIB/log4j-api-2.17.1.jar:$LIB/slf4j-api-1.7.32.jar:$LIB/commons-logging-1.2.jar"
find "$SRC" -name '*.java' > /tmp/mnb-toolkit-sources.txt
javac --release 11 -cp "$CP" -d "$OUT" @/tmp/mnb-toolkit-sources.txt
echo "Compiled OK → $OUT"
find "$OUT" -type f
