#!/usr/bin/env bash
# Ensure pluginsrc/mnb-iam-toolkit/dist/${PLUGIN_NAME}-${PLUGIN_VER}.zip exists.
#
# Order:
#   1) dist zip already present
#   2) copy from ssdplugins/ (committed convenience zips)
#   3) stage IIQ libs (SSB extract or running container) + package.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PLUGIN="$ROOT/pluginsrc/mnb-iam-toolkit"
# shellcheck source=version.env
source "$PLUGIN/version.env"
DIST="$PLUGIN/dist"
ZIP="$DIST/${PLUGIN_NAME}-${PLUGIN_VER}.zip"
SSD="$ROOT/ssdplugins/${PLUGIN_NAME}"

mkdir -p "$DIST"

if [[ -f "$ZIP" ]]; then
  echo "Plugin zip ready → $ZIP"
  exit 0
fi

# Prefer versioned ssdplugins zip, then unversioned alias
for cand in \
  "$SSD/${PLUGIN_NAME}-${PLUGIN_VER}.zip" \
  "$SSD/${PLUGIN_NAME}.zip"
do
  if [[ -f "$cand" ]]; then
    echo "Using committed plugin zip → $cand"
    cp "$cand" "$ZIP"
    # Keep unversioned alias in dist for callers that expect it
    cp "$cand" "$DIST/${PLUGIN_NAME}.zip"
    echo "Plugin zip ready → $ZIP"
    exit 0
  fi
done

echo "No prebuilt zip — packaging from source…"
"$PLUGIN/stage-iiq-libs.sh"
"$PLUGIN/package.sh"
if [[ ! -f "$ZIP" ]]; then
  echo "ERROR: package.sh did not produce $ZIP" >&2
  exit 1
fi
echo "Plugin zip ready → $ZIP"
