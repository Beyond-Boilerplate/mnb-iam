#!/usr/bin/env bash
# Tear down IdentityIQ local lab created by setup-local.sh
#
# Usage:
#   ./tools/lab/teardown-local.sh --yes
#   ./tools/lab/teardown-local.sh --yes --purge-mysql   # also remove brew/apt mysql packages when possible
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/lib/common.sh"

ASSUME_YES=0
KEEP_MYSQL=1
PURGE_MYSQL=0
REMOVE_ALIASES=1

usage() {
  cat <<'EOF'
IdentityIQ local teardown (macOS / Linux / WSL)

Removes:
  - Running Tomcat on the lab HTTP port
  - Lab MySQL process (port 3307 by default)
  - $IIQ_LAB_HOME (Tomcat + exploded WAR + lab MySQL datadir + portable JDK/MySQL)
  - ~/.iiq-lab state
  - Aliases block from ~/.zshrc and ~/.bashrc

Windows native: use scripts\teardown-local.ps1

Options:
  --yes            Skip confirmation
  --keep-mysql     Keep MySQL packages installed (default)
  --purge-mysql    Also uninstall mysql@8.4 / mysql-server packages when possible
  --keep-aliases   Leave aliases in shell rc files
  -h, --help       Show help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --yes|-y) ASSUME_YES=1 ;;
    --keep-mysql) KEEP_MYSQL=1; PURGE_MYSQL=0 ;;
    --purge-mysql) PURGE_MYSQL=1; KEEP_MYSQL=0 ;;
    --keep-aliases) REMOVE_ALIASES=0 ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown option: $1" ;;
  esac
  shift
done

detect_os
if is_gitbash; then
  die "Use PowerShell on Windows: .\\scripts\\teardown-local.ps1 -Yes"
fi

load_lab_env

SAILPOINT_ROOT="${SAILPOINT_ROOT:-$(iiq_repo_root)}"
IIQ_LAB_HOME="${IIQ_LAB_HOME:-$HOME/iiq-lab}"
CATALINA_HOME="${CATALINA_HOME:-$IIQ_LAB_HOME/tomcat}"
IIQ_HTTP_PORT="${IIQ_HTTP_PORT:-8080}"

if [[ "$ASSUME_YES" -ne 1 ]]; then
  cat <<EOF
This will tear down the IdentityIQ lab:
  Lab home:  $IIQ_LAB_HOME
  Tomcat:    $CATALINA_HOME
  HTTP port: $IIQ_HTTP_PORT
  DB port:   ${IIQ_DB_PORT:-3307}
  State:     $IIQ_LAB_STATE_DIR
  Purge MySQL packages: $([[ "$PURGE_MYSQL" -eq 1 ]] && echo YES || echo no)
EOF
  read -r -p "Type 'teardown' to continue: " ans
  [[ "$ans" == "teardown" ]] || die "Aborted"
fi

log "Stopping Tomcat (if running)…"
if [[ -x "${CATALINA_HOME}/bin/shutdown.sh" ]]; then
  "$CATALINA_HOME/bin/shutdown.sh" >/dev/null 2>&1 || true
  sleep 2
fi
if port_in_use "$IIQ_HTTP_PORT"; then
  pids="$(lsof -nP -iTCP:"$IIQ_HTTP_PORT" -sTCP:LISTEN -t 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    warn "Killing listeners on :$IIQ_HTTP_PORT → $pids"
    # shellcheck disable=SC2086
    kill $pids 2>/dev/null || true
    sleep 1
  fi
fi

log "Stopping lab MySQL (if running)…"
if [[ -n "${IIQ_MYSQL_PID:-}" && -f "${IIQ_MYSQL_PID}" ]]; then
  kill "$(cat "$IIQ_MYSQL_PID")" 2>/dev/null || true
  rm -f "$IIQ_MYSQL_PID"
fi
dbport="${IIQ_DB_PORT:-3307}"
if port_in_use "$dbport"; then
  lab_mysql_pids="$(lsof -nP -iTCP:"$dbport" -sTCP:LISTEN -t 2>/dev/null || true)"
  if [[ -n "$lab_mysql_pids" ]]; then
    warn "Stopping MySQL listeners on :$dbport → $lab_mysql_pids"
    # shellcheck disable=SC2086
    kill $lab_mysql_pids 2>/dev/null || true
    sleep 1
  fi
fi

log "Lab MySQL datadir will be removed with \$IIQ_LAB_HOME"

log "Removing lab home $IIQ_LAB_HOME …"
rm -rf "$IIQ_LAB_HOME"

log "Removing state dir $IIQ_LAB_STATE_DIR …"
rm -rf "$IIQ_LAB_STATE_DIR"

if [[ "$REMOVE_ALIASES" -eq 1 ]]; then
  marker="# >>> identityiq-lab aliases >>>"
  end_marker="# <<< identityiq-lab aliases <<<"
  for local_rc in "$HOME/.zshrc" "$HOME/.bashrc"; do
    if [[ -f "$local_rc" ]] && grep -qF "$marker" "$local_rc"; then
      tmp="$(mktemp)"
      awk -v m="$marker" -v e="$end_marker" '
        $0==m {skip=1; next}
        $0==e {skip=0; next}
        !skip {print}
      ' "$local_rc" >"$tmp"
      mv "$tmp" "$local_rc"
      log "Removed aliases block from $local_rc"
    fi
  done
fi

if [[ "$PURGE_MYSQL" -eq 1 ]]; then
  if command -v brew >/dev/null 2>&1; then
    log "Uninstalling mysql@8.4 via Homebrew…"
    brew services stop mysql@8.4 2>/dev/null || true
    brew uninstall mysql@8.4 2>/dev/null || warn "brew uninstall mysql@8.4 failed / not installed"
  elif command -v apt-get >/dev/null 2>&1; then
    warn "Leaving apt mysql-server installed (shared system package). Remove manually if desired:"
    warn "  sudo apt-get remove --purge mysql-server"
  fi
fi

cat <<EOF

============================================
 IdentityIQ lab teardown complete
============================================
 Remaining (by design):
   - Repo at $SAILPOINT_ROOT
   - System JDK / Homebrew installs (unless purged)
   - Your system MySQL on :3306 (untouched)

 Re-setup:
   ./tools/lab/setup-local.sh
   # Windows: .\\scripts\\setup-local.ps1
============================================
EOF
