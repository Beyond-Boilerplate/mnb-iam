#!/usr/bin/env bash
# Verify the public academy and IdentityIQ routes with bounded, diagnostic retries.
# Academy should be fast; IdentityIQ may return 502/503/504 for several minutes while Tomcat starts.
set -euo pipefail

LEARN_SMOKE_URL="${LEARN_SMOKE_URL:-https://sailpoint.lmsapp.us/}"
IIQ_SMOKE_URL="${IIQ_SMOKE_URL:-https://sailpoint.lmsapp.us/identityiq/login.jsf}"
ACADEMY_SMOKE_ATTEMPTS="${ACADEMY_SMOKE_ATTEMPTS:-6}"
ACADEMY_SMOKE_INTERVAL_SECONDS="${ACADEMY_SMOKE_INTERVAL_SECONDS:-5}"
IIQ_SMOKE_ATTEMPTS="${IIQ_SMOKE_ATTEMPTS:-24}"
IIQ_SMOKE_INTERVAL_SECONDS="${IIQ_SMOKE_INTERVAL_SECONDS:-15}"
SMOKE_REQUEST_TIMEOUT_SECONDS="${SMOKE_REQUEST_TIMEOUT_SECONDS:-20}"
ACADEMY_PATTERN="${ACADEMY_PATTERN:-Meridian|IAM Academy|Curriculum}"
BODY_DIR="$(mktemp -d)"
trap 'rm -rf "$BODY_DIR"' EXIT

diagnose_failure() {
  local label="$1" url="$2" code="$3" body_file="$4" attempts="$5"
  echo "::error title=${label} smoke failed::${url} returned HTTP ${code} after ${attempts} attempts"
  case "${label}:${code}" in
    academy:404|academy:200)
      echo "The public hostname may bypass sailpoint-edge or serve the wrong upstream."
      echo "Cloudflare target: sailpoint-edge.sailpoint.svc.cluster.local:8080"
      ;;
    iiq:502|iiq:503|iiq:504|iiq:000)
      echo "Cloudflare reaches sailpoint-edge (or times out), but the IdentityIQ upstream is unavailable."
      echo "Check deploy/identityiq readiness, service endpoints, and sailpoint-edge logs."
      echo "IIQ often needs several minutes after Helm upgrade before login.jsf returns 200/302."
      ;;
  esac
  if [[ -s "$body_file" ]]; then
    echo "Response preview:"
    cut -c 1-300 "$body_file" || true
  fi
}

probe() {
  local url="$1" label="$2" attempts="$3" interval="$4"
  local body_file="${BODY_DIR}/${label}.body"
  local attempt code="000" reason

  for ((attempt = 1; attempt <= attempts; attempt++)); do
    : >"$body_file"
    if ! code=$(curl --silent --show-error \
      --output "$body_file" \
      --write-out '%{http_code}' \
      --connect-timeout 10 \
      --max-time "$SMOKE_REQUEST_TIMEOUT_SECONDS" \
      "$url"); then
      code="000"
    fi

    reason=""
    if [[ "$label" == "academy" ]]; then
      if [[ "$code" == "200" ]] && grep -qiE "$ACADEMY_PATTERN" "$body_file"; then
        echo "${label} attempt ${attempt}: HTTP ${code}, expected academy content found"
        return 0
      fi
      [[ "$code" == "200" ]] && reason=" (unexpected content)"
    elif [[ "$code" =~ ^(200|301|302|303)$ ]]; then
      echo "${label} attempt ${attempt}: HTTP ${code}"
      return 0
    fi

    echo "${label} attempt ${attempt}/${attempts}: HTTP ${code}${reason}"
    if ((attempt < attempts)); then
      sleep "$interval"
    fi
  done

  diagnose_failure "$label" "$url" "$code" "$body_file" "$attempts"
  return 1
}

probe "$LEARN_SMOKE_URL" academy "$ACADEMY_SMOKE_ATTEMPTS" "$ACADEMY_SMOKE_INTERVAL_SECONDS"
probe "$IIQ_SMOKE_URL" iiq "$IIQ_SMOKE_ATTEMPTS" "$IIQ_SMOKE_INTERVAL_SECONDS"
echo "Public academy and IdentityIQ routes are healthy."
