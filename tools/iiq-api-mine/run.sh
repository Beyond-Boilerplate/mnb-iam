#!/usr/bin/env bash
# Mine IIQ JAX-RS APIs and regenerate docs/api OpenAPI YAML.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$(dirname "$0")"
export PYTHONPATH="."
if [[ ! -f "$ROOT/build/extract/WEB-INF/lib/identityiq.jar" ]]; then
  echo "ERROR: identityiq.jar not found under build/extract. Run ./build.sh clean war first." >&2
  exit 1
fi
python3 mine_jaxrs.py --war-lib "$ROOT/build/extract/WEB-INF/lib" --out "$ROOT/docs/api/inventory/mined-endpoints.json"
python3 generate_openapi.py --inventory "$ROOT/docs/api/inventory/mined-endpoints.json" --out-dir "$ROOT/docs/api/openapi"
python3 generate_gaps.py --inventory "$ROOT/docs/api/inventory/mined-endpoints.json" --out "$ROOT/docs/api/GAPS.md"
echo "Done. Browse docs/api/swagger/index.html"
