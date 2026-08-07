#!/usr/bin/env bash
# Build installable IdentityIQ plugin ZIP for mnb-iam-toolkit.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PLUGIN="$ROOT/pluginsrc/mnb-iam-toolkit"
DIST="$PLUGIN/dist"
# shellcheck source=version.env
source "$PLUGIN/version.env"
NAME="$PLUGIN_NAME"
VER="$PLUGIN_VER"

"$PLUGIN/compile.sh"

STAGE="$(mktemp -d)"
cleanup() { rm -rf "$STAGE"; }
trap cleanup EXIT

mkdir -p "$STAGE/import/install" "$STAGE/ui/css" "$STAGE/ui/js" "$DIST"

# manifest at zip root
cp "$PLUGIN/manifest.xml" "$STAGE/manifest.xml"

# classes → plugin jar (IIQ expects a jar next to manifest)
jar cf "$STAGE/${NAME}.jar" -C "$PLUGIN/build/classes" .

# install-time objects
cp "$PLUGIN/import/install/"*.xml "$STAGE/import/install/"

# optional UI assets
cp "$PLUGIN/ui/css/"* "$STAGE/ui/css/" 2>/dev/null || true
cp "$PLUGIN/ui/js/"* "$STAGE/ui/js/" 2>/dev/null || true

ZIP="$DIST/${NAME}-${VER}.zip"
rm -f "$ZIP"
( cd "$STAGE" && zip -qr "$ZIP" manifest.xml "${NAME}.jar" import ui )

# convenience copy for SSB plugin drop folder
mkdir -p "$ROOT/ssdplugins/mnb_iam_toolkit"
cp "$ZIP" "$ROOT/ssdplugins/mnb_iam_toolkit/${NAME}-${VER}.zip"
cp "$ZIP" "$ROOT/ssdplugins/mnb_iam_toolkit/${NAME}.zip"

echo "Built $ZIP"
unzip -l "$ZIP"
