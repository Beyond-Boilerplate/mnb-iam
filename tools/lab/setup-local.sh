#!/usr/bin/env bash
# IdentityIQ 8.5 — greenfield local lab setup (macOS / Linux / WSL)
#
# Bootstraps missing tools on a blank machine, then deploys IdentityIQ.
# Windows native: use setup-local.ps1 instead.
#
# Usage:
#   ./tools/lab/setup-local.sh
#   ./tools/lab/setup-local.sh --check
#   ./tools/lab/setup-local.sh --force-db
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/lib/common.sh"

usage() {
  cat <<'EOF'
IdentityIQ local setup (macOS / Linux / WSL)

On a brand-new machine this script bootstraps missing tools:
  - Homebrew (macOS) or apt/dnf packages (Linux)
  - JDK 11 (package or portable Temurin)
  - MySQL 8.4 (package or portable tarball) on lab port 3307
  - Apache Tomcat 9 (downloaded into ~/iiq-lab)

Windows native: use tools\lab\setup-local.ps1 instead.

Options:
  --skip-import     Skip iiq console import of init.xml / init-lcm.xml
  --no-start        Do not start Tomcat at the end
  --force-db        Drop and recreate IdentityIQ databases
  --no-aliases      Do not wire aliases into shell rc
  --check           Preflight only (detect OS / tools; do not install)
  -h, --help        Show help
EOF
}

SKIP_IMPORT=0
NO_START=0
FORCE_DB=0
INSTALL_ALIASES=1
CHECK_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-import) SKIP_IMPORT=1 ;;
    --no-start) NO_START=1 ;;
    --force-db) FORCE_DB=1 ;;
    --no-aliases) INSTALL_ALIASES=0 ;;
    --check) CHECK_ONLY=1 ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown option: $1" ;;
  esac
  shift
done

SAILPOINT_ROOT="$(iiq_repo_root)"
# SSD layout: GA binary lives in base/ga/identityiq-${version}.zip
GA_ZIP="$SAILPOINT_ROOT/base/ga/identityiq-8.5.zip"
WAR_PATH="$SAILPOINT_ROOT/base/ga/.work/identityiq.war"
SQL_CREATE="$SAILPOINT_ROOT/docs/vendor/iiq-8.5/database/create_identityiq_tables-8.5.mysql"
SQL_DROP="$SAILPOINT_ROOT/docs/vendor/iiq-8.5/database/drop_identityiq_tables-8.5.mysql"
# Fallback if vendor DB scripts missing (SSB db/ or legacy)
if [[ ! -f "$SQL_CREATE" ]]; then
  SQL_CREATE="$SAILPOINT_ROOT/db/mysql/create_identityiq_tables-8.5.mysql"
fi
if [[ ! -f "$SQL_DROP" ]]; then
  SQL_DROP="$SAILPOINT_ROOT/docs/vendor/iiq-8.5/database/drop_identityiq_tables-8.5.mysql"
fi
IIQ_LAB_DATA="${IIQ_LAB_DATA:-$IIQ_LAB_HOME/data}"
CATALINA_HOME="${CATALINA_HOME:-$IIQ_LAB_HOME/tomcat}"
IIQ_HOME="${IIQ_HOME:-$CATALINA_HOME/webapps/identityiq}"
IIQ_INSTALLED_MYSQL=0
IIQ_INSTALLED_TOMCAT=0
IIQ_INSTALLED_JDK=0

mkdir -p "$IIQ_LAB_STATE_DIR" "$IIQ_LAB_LOG_DIR" "$IIQ_LAB_HOME" "$IIQ_LAB_DATA"

ensure_ga_war() {
  [[ -f "$GA_ZIP" ]] || die "Missing GA zip: $GA_ZIP
Place SailPoint IdentityIQ 8.5 GA zip at base/ga/identityiq-8.5.zip (SSD layout).
It must contain identityiq.war."
  mkdir -p "$(dirname "$WAR_PATH")"
  if [[ ! -f "$WAR_PATH" || "$GA_ZIP" -nt "$WAR_PATH" ]]; then
    log "Extracting identityiq.war from $GA_ZIP …"
    rm -f "$WAR_PATH"
    unzip -p "$GA_ZIP" identityiq.war >"$WAR_PATH" \
      || die "Could not extract identityiq.war from $GA_ZIP"
  fi
}

if [[ "$CHECK_ONLY" -eq 1 ]]; then
  detect_os
  echo "Platform: $IIQ_PLATFORM ($IIQ_OS / $IIQ_ARCH)"
  echo "Repo:     $SAILPOINT_ROOT"
  echo "GA zip:   $([[ -f $GA_ZIP ]] && echo OK || echo MISSING)"
  echo "SQL:      $([[ -f $SQL_CREATE ]] && echo OK || echo MISSING)"
  echo "curl:     $(command -v curl >/dev/null && echo OK || echo MISSING)"
  echo "brew:     $(command -v brew >/dev/null && echo OK || echo missing)"
  echo "java:     $(command -v java >/dev/null && java -version 2>&1 | head -1 || echo missing)"
  echo "mysql:    $(command -v mysql >/dev/null && mysql --version || echo missing)"
  echo "Tip: run without --check to bootstrap + install. Day-2 builds: ./build.sh -Dtarget=sandbox clean war"
  exit 0
fi

SETUP_LOG="$IIQ_LAB_LOG_DIR/setup-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$SETUP_LOG") 2>&1

log "SailPoint root: $SAILPOINT_ROOT"
log "Lab home:       $IIQ_LAB_HOME"
log "Setup log:      $SETUP_LOG"

ensure_ga_war
[[ -f "$WAR_PATH" ]] || die "Missing WAR after extract: $WAR_PATH"
[[ -f "$SQL_CREATE" ]] || die "Missing SQL: $SQL_CREATE
Expected docs/vendor/iiq-8.5/database/create_identityiq_tables-8.5.mysql"

# ---------------------------------------------------------------------------
# 0) Greenfield bootstrap (no tools → install them)
# ---------------------------------------------------------------------------
bootstrap_prerequisites

# Prefer JDK 11 major for IIQ 8.5
JAVA_MAJOR="$("$JAVA_HOME/bin/java" -version 2>&1 | head -1 | sed -E 's/.*version "([0-9]+)(\.[0-9]+)*.*/\1/')"
if [[ "$JAVA_MAJOR" == "1" ]]; then
  JAVA_MAJOR="$("$JAVA_HOME/bin/java" -version 2>&1 | head -1 | sed -E 's/.*version "1\.([0-9]+).*/\1/')"
fi
if [[ "${JAVA_MAJOR:-0}" -gt 17 ]]; then
  warn "JAVA_HOME is Java $JAVA_MAJOR. IdentityIQ 8.5 is validated on 11/17 — installing/preferring JDK 11…"
  ensure_java_portable_or_pkg
fi

# ---------------------------------------------------------------------------
# 2) MySQL lab instance (dedicated datadir/port — avoids locked system MySQL)
# ---------------------------------------------------------------------------
ensure_mysql() {
  resolve_mysql_bin_dir

  # Lab-managed datadir/socket/port — never fight system MySQL on 3306
  IIQ_DB_PORT="${IIQ_DB_PORT:-3307}"
  IIQ_MYSQL_DATA="${IIQ_MYSQL_DATA:-$IIQ_LAB_HOME/mysql/data}"
  IIQ_MYSQL_SOCKET="${IIQ_MYSQL_SOCKET:-$IIQ_LAB_HOME/mysql/mysql.sock}"
  IIQ_MYSQL_PID="${IIQ_MYSQL_PID:-$IIQ_LAB_HOME/mysql/mysqld.pid}"
  IIQ_MYSQL_ERR="${IIQ_MYSQL_ERR:-$IIQ_LAB_HOME/mysql/mysqld.err}"
  IIQ_USE_LAB_MYSQL=1
  export IIQ_DB_PORT IIQ_MYSQL_DATA IIQ_MYSQL_SOCKET IIQ_MYSQL_PID IIQ_USE_LAB_MYSQL

  mkdir -p "$(dirname "$IIQ_MYSQL_DATA")" "$IIQ_LAB_HOME/mysql"

  local mysqld
  mysqld="$(mysqld_bin)"

  if [[ ! -d "$IIQ_MYSQL_DATA/mysql" ]]; then
    log "Initializing lab MySQL datadir at $IIQ_MYSQL_DATA …"
    rm -rf "$IIQ_MYSQL_DATA"
    mkdir -p "$IIQ_MYSQL_DATA"
    local basedir
    basedir="$(cd "$(dirname "$mysqld")/.." && pwd)"
    "$mysqld" \
      --initialize-insecure \
      --datadir="$IIQ_MYSQL_DATA" \
      --basedir="$basedir"
  fi

  if ! mysql_root_ok; then
    if port_in_use "$IIQ_DB_PORT"; then
      local alt
      for alt in 3307 3308 3309 3310; do
        if ! port_in_use "$alt"; then
          IIQ_DB_PORT="$alt"
          export IIQ_DB_PORT
          break
        fi
      done
    fi

    local basedir
    basedir="$(cd "$(dirname "$mysqld")/.." && pwd)"
    log "Starting lab MySQL on 127.0.0.1:${IIQ_DB_PORT} (socket $IIQ_MYSQL_SOCKET)…"
    nohup "$mysqld" \
      --datadir="$IIQ_MYSQL_DATA" \
      --basedir="$basedir" \
      --port="$IIQ_DB_PORT" \
      --bind-address=127.0.0.1 \
      --socket="$IIQ_MYSQL_SOCKET" \
      --pid-file="$IIQ_MYSQL_PID" \
      --mysqlx=0 \
      >>"$IIQ_MYSQL_ERR" 2>&1 &

    local i=0
    until mysql_root_ok; do
      i=$((i + 1))
      if (( i > 45 )); then
        warn "Lab MySQL failed to start. Last log lines:"
        tail -n 40 "$IIQ_MYSQL_ERR" || true
        die "Lab MySQL did not become ready on port $IIQ_DB_PORT"
      fi
      sleep 2
    done
  else
    log "Lab MySQL already accepting connections"
  fi

  log "MySQL is ready ($(mysql_root -N -e 'SELECT VERSION()')) on port $IIQ_DB_PORT"
}

ensure_mysql

# ---------------------------------------------------------------------------
# 3) Databases
# ---------------------------------------------------------------------------
create_databases() {
  if [[ "$FORCE_DB" -eq 1 ]]; then
    log "Dropping existing IdentityIQ schemas (--force-db)…"
    if [[ -f "$SQL_DROP" ]]; then
      mysql_root <"$SQL_DROP" || warn "Drop script reported errors (continuing)"
    fi
    mysql_root -e "DROP DATABASE IF EXISTS identityiq; DROP DATABASE IF EXISTS identityiqah; DROP DATABASE IF EXISTS identityiqPlugin;" || true
  fi

  local count
  count="$(mysql_root -N -e "SHOW DATABASES LIKE 'identityiq';" | wc -l | tr -d ' ')"
  if [[ "$count" -ge 1 && "$FORCE_DB" -eq 0 ]]; then
    log "Database identityiq already exists — skipping create (use --force-db to recreate)"
  else
    log "Creating IdentityIQ schemas (this can take a minute)…"
    # MySQL 8.4 disables mysql_native_password by default — rewrite to caching_sha2_password
    local tmp_sql
    tmp_sql="$(mktemp)"
    sed -E 's/IDENTIFIED WITH mysql_native_password BY/IDENTIFIED WITH caching_sha2_password BY/g' \
      "$SQL_CREATE" >"$tmp_sql"
    mysql_root <"$tmp_sql"
    rm -f "$tmp_sql"
    log "Schemas created"
  fi

  # Ensure users can connect via TCP 127.0.0.1 (JDBC) as well as socket
  mysql_root <<SQL
CREATE USER IF NOT EXISTS 'identityiq'@'127.0.0.1' IDENTIFIED WITH caching_sha2_password BY 'identityiq';
GRANT ALL PRIVILEGES ON identityiq.* TO 'identityiq'@'127.0.0.1';
CREATE USER IF NOT EXISTS 'identityiqah'@'127.0.0.1' IDENTIFIED WITH caching_sha2_password BY 'identityiqah';
GRANT ALL PRIVILEGES ON identityiqah.* TO 'identityiqah'@'127.0.0.1';
CREATE USER IF NOT EXISTS 'identityiqPlugin'@'127.0.0.1' IDENTIFIED WITH caching_sha2_password BY 'identityiqPlugin';
GRANT ALL PRIVILEGES ON identityiqPlugin.* TO 'identityiqPlugin'@'127.0.0.1';
FLUSH PRIVILEGES;
SQL

  mysql_root -e "SHOW DATABASES LIKE 'identityiq%';"
}

create_databases

# ---------------------------------------------------------------------------
# 4) Tomcat 9
# ---------------------------------------------------------------------------
ensure_tomcat() {
  if [[ -x "$CATALINA_HOME/bin/catalina.sh" ]]; then
    log "Tomcat already present at $CATALINA_HOME"
    return
  fi

  local ver="$IIQ_TOMCAT_VERSION"
  local base="https://dlcdn.apache.org/tomcat/tomcat-9/v${ver}/bin/apache-tomcat-${ver}.tar.gz"
  local archive_fallback="https://archive.apache.org/dist/tomcat/tomcat-9/v${ver}/bin/apache-tomcat-${ver}.tar.gz"
  local tgz="$IIQ_LAB_HOME/apache-tomcat-${ver}.tar.gz"

  log "Downloading Apache Tomcat ${ver}…"
  if ! curl -fL --retry 3 -o "$tgz" "$base"; then
    warn "Primary CDN failed; trying archive.apache.org…"
    curl -fL --retry 3 -o "$tgz" "$archive_fallback"
  fi

  mkdir -p "$IIQ_LAB_HOME"
  tar -xzf "$tgz" -C "$IIQ_LAB_HOME"
  rm -f "$tgz"

  # Normalize to $IIQ_LAB_HOME/tomcat
  if [[ -d "$IIQ_LAB_HOME/apache-tomcat-${ver}" ]]; then
    rm -rf "$CATALINA_HOME"
    mv "$IIQ_LAB_HOME/apache-tomcat-${ver}" "$CATALINA_HOME"
  fi
  [[ -x "$CATALINA_HOME/bin/catalina.sh" ]] || die "Tomcat install failed at $CATALINA_HOME"
  IIQ_INSTALLED_TOMCAT=1
  log "Tomcat installed → $CATALINA_HOME"
}

ensure_tomcat

# Configure port + heap
configure_tomcat() {
  mkdir -p "$CATALINA_HOME/bin"
  cat >"$CATALINA_HOME/bin/setenv.sh" <<EOF
#!/bin/sh
# IdentityIQ lab setenv — managed by setup-local.sh
export JAVA_HOME="$JAVA_HOME"
export JAVA_OPTS="-Xms${IIQ_HEAP_MS} -Xmx${IIQ_HEAP_MX} -Djava.awt.headless=true -Dfile.encoding=UTF-8 --add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.lang.invoke=ALL-UNNAMED --add-exports=java.naming/com.sun.jndi.ldap=ALL-UNNAMED"
EOF
  chmod +x "$CATALINA_HOME/bin/setenv.sh"

  # Adjust HTTP connector port if needed
  local server_xml="$CATALINA_HOME/conf/server.xml"
  if [[ -f "$server_xml" ]] && [[ "$IIQ_HTTP_PORT" != "8080" ]]; then
    if grep -q 'Connector port="8080"' "$server_xml"; then
      sed -i.bak "s/Connector port=\"8080\"/Connector port=\"${IIQ_HTTP_PORT}\"/" "$server_xml"
      log "Tomcat HTTP port set to $IIQ_HTTP_PORT"
    fi
  fi
}

configure_tomcat

# ---------------------------------------------------------------------------
# 5) Deploy WAR
# ---------------------------------------------------------------------------
deploy_war() {
  log "Deploying identityiq.war → $IIQ_HOME"
  # Stop tomcat if running on our port
  if lsof -nP -iTCP:"$IIQ_HTTP_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    log "Stopping existing process on port $IIQ_HTTP_PORT…"
    "$CATALINA_HOME/bin/shutdown.sh" >/dev/null 2>&1 || true
    sleep 3
    # Force-kill leftovers on our port if still listening
    local pids
    pids="$(lsof -nP -iTCP:"$IIQ_HTTP_PORT" -sTCP:LISTEN -t 2>/dev/null || true)"
    if [[ -n "$pids" ]]; then
      warn "Force-killing PIDs still on :$IIQ_HTTP_PORT → $pids"
      # shellcheck disable=SC2086
      kill $pids 2>/dev/null || true
      sleep 2
    fi
  fi

  rm -rf "$IIQ_HOME"
  mkdir -p "$IIQ_HOME"
  (
    cd "$IIQ_HOME"
    jar xf "$WAR_PATH"
  )
  chmod +x "$IIQ_HOME/WEB-INF/bin/iiq" || true
  [[ -f "$IIQ_HOME/WEB-INF/classes/iiq.properties" ]] || die "Deploy failed — iiq.properties missing"
  log "WAR exploded ($(du -sh "$IIQ_HOME" | awk '{print $1}'))"
}

deploy_war

# ---------------------------------------------------------------------------
# 6) iiq.properties (lab plaintext passwords)
# ---------------------------------------------------------------------------
configure_iiq_properties() {
  local props="$IIQ_HOME/WEB-INF/classes/iiq.properties"
  local bak="$props.bak.$(date +%Y%m%d%H%M%S)"
  cp "$props" "$bak"
  log "Configuring $props (backup: $bak)"

  # Use Python for reliable property edits
  JAVA_HOME="$JAVA_HOME" IIQ_DB_HOST="$IIQ_DB_HOST" IIQ_DB_PORT="$IIQ_DB_PORT" \
  IIQ_DB_NAME="$IIQ_DB_NAME" IIQ_DB_USER="$IIQ_DB_USER" IIQ_DB_PASS="$IIQ_DB_PASS" \
  IIQ_DB_AH_NAME="$IIQ_DB_AH_NAME" IIQ_DB_AH_USER="$IIQ_DB_AH_USER" IIQ_DB_AH_PASS="$IIQ_DB_AH_PASS" \
  IIQ_DB_PLUGIN_NAME="$IIQ_DB_PLUGIN_NAME" IIQ_DB_PLUGIN_USER="$IIQ_DB_PLUGIN_USER" IIQ_DB_PLUGIN_PASS="$IIQ_DB_PLUGIN_PASS" \
  PROPS_PATH="$props" python3 - <<'PY'
import os, re
path = os.environ["PROPS_PATH"]
host = os.environ["IIQ_DB_HOST"]
port = os.environ["IIQ_DB_PORT"]

def mysql_url(db):
    return (
        f"jdbc:mysql://{host}:{port}/{db}"
        "?useServerPrepStmts=true&tinyInt1isBit=true&useSSL=false"
        "&characterEncoding=UTF-8&serverTimezone=UTC&allowPublicKeyRetrieval=true"
    )

replacements = {
    "dataSource.username": os.environ["IIQ_DB_USER"],
    "dataSource.password": os.environ["IIQ_DB_PASS"],
    "dataSource.url": mysql_url(os.environ["IIQ_DB_NAME"]),
    "dataSource.driverClassName": "com.mysql.cj.jdbc.Driver",
    "pluginsDataSource.username": os.environ["IIQ_DB_PLUGIN_USER"],
    "pluginsDataSource.password": os.environ["IIQ_DB_PLUGIN_PASS"],
    "pluginsDataSource.url": mysql_url(os.environ["IIQ_DB_PLUGIN_NAME"]),
    "pluginsDataSource.driverClassName": "com.mysql.cj.jdbc.Driver",
    "dataSourceAccessHistory.username": os.environ["IIQ_DB_AH_USER"],
    "dataSourceAccessHistory.password": os.environ["IIQ_DB_AH_PASS"],
    "dataSourceAccessHistory.url": mysql_url(os.environ["IIQ_DB_AH_NAME"]),
    "dataSourceAccessHistory.driverClassName": "com.mysql.cj.jdbc.Driver",
}

text = open(path, encoding="utf-8").read().splitlines(True)
out = []
for line in text:
    stripped = line.lstrip()
    if stripped.startswith("#") or "=" not in line:
        out.append(line)
        continue
    key = stripped.split("=", 1)[0].strip()
    if key in replacements:
        # preserve indentation
        indent = line[: len(line) - len(stripped)]
        out.append(f"{indent}{key}={replacements[key]}\n")
    else:
        out.append(line)

# Ensure MySQL dialect is active (uncomment if needed / leave others alone)
joined = "".join(out)
dialect = "sessionFactory.hibernateProperties.hibernate.dialect=org.hibernate.dialect.MySQL57Dialect"
if "MySQL57Dialect" not in joined:
    joined += "\n" + dialect + "\n"

open(path, "w", encoding="utf-8").write(joined)
print("iiq.properties updated")
PY
}

configure_iiq_properties

# ---------------------------------------------------------------------------
# 7) Import init.xml (and LCM)
# ---------------------------------------------------------------------------
import_init() {
  if [[ "$SKIP_IMPORT" -eq 1 ]]; then
    log "Skipping object import (--skip-import)"
    return
  fi

  # Check if already initialized (spadmin identity table row heuristic)
  local inited
  inited="$(mysql_root -N -e "SELECT COUNT(*) FROM identityiq.spt_identity WHERE name='spadmin';" 2>/dev/null || echo 0)"
  if [[ "$inited" != "0" && "$FORCE_DB" -eq 0 ]]; then
    log "IdentityIQ already initialized (spadmin exists) — skipping import (use --force-db to rebuild)"
    return
  fi

  log "Importing init.xml via iiq console (several minutes)…"
  export JAVA_HOME PATH="$JAVA_HOME/bin:$PATH" SPHOME="$IIQ_HOME"
  local iiq_bin="$IIQ_HOME/WEB-INF/bin/iiq"
  chmod +x "$iiq_bin"

  # Non-interactive import
  (
    cd "$IIQ_HOME/WEB-INF/bin"
    printf 'import init.xml\nquit\n' | ./iiq console
  )

  if [[ "$IIQ_IMPORT_LCM" == "1" ]]; then
    log "Importing init-lcm.xml…"
    (
      cd "$IIQ_HOME/WEB-INF/bin"
      printf 'import init-lcm.xml\nquit\n' | ./iiq console
    ) || warn "init-lcm.xml import failed — LCM lessons may need manual import"
  fi

  inited="$(mysql_root -N -e "SELECT COUNT(*) FROM identityiq.spt_identity WHERE name='spadmin';" 2>/dev/null || echo 0)"
  [[ "$inited" != "0" ]] || die "Import finished but spadmin identity not found — check $SETUP_LOG"
  log "Import OK (spadmin present)"
}

import_init

# ---------------------------------------------------------------------------
# 8) Lab data + aliases + env
# ---------------------------------------------------------------------------
copy_lab_data() {
  local src_data="$SAILPOINT_ROOT/lab-data"
  for f in HRApplications.txt EmployeeData.txt email.txt; do
    if [[ -f "$src_data/$f" ]]; then
      cp "$src_data/$f" "$IIQ_LAB_DATA/"
    elif [[ -f "$SAILPOINT_ROOT/$f" ]]; then
      cp "$SAILPOINT_ROOT/$f" "$IIQ_LAB_DATA/"
    fi
  done
  log "Lab data → $IIQ_LAB_DATA"
}

copy_lab_data
save_lab_env

install_aliases() {
  [[ "$INSTALL_ALIASES" -eq 1 ]] || return 0
  local marker="# >>> identityiq-lab aliases >>>"
  local end_marker="# <<< identityiq-lab aliases <<<"
  local block rc
  block=$(cat <<EOF

$marker
# IdentityIQ local lab — managed by $SAILPOINT_ROOT/tools/lab/setup-local.sh
export IIQ_LAB_ENV_FILE="$IIQ_LAB_ENV_FILE"
[[ -f "\$IIQ_LAB_ENV_FILE" ]] && source "\$IIQ_LAB_ENV_FILE"
source "$SAILPOINT_ROOT/tools/lab/iiq-aliases.sh"
$end_marker
EOF
)
  local wired=()
  for rc in "$HOME/.zshrc" "$HOME/.bashrc"; do
    # On macOS default is zsh; on Linux often bash. Wire both when present or create zshrc.
    if [[ "$rc" == "$HOME/.bashrc" && ! -f "$rc" && "${IIQ_PLATFORM:-}" == "macos" ]]; then
      continue
    fi
    [[ -f "$rc" ]] || touch "$rc"
    if grep -qF "$marker" "$rc"; then
      local tmp
      tmp="$(mktemp)"
      awk -v m="$marker" -v e="$end_marker" '
        $0==m {skip=1; next}
        $0==e {skip=0; next}
        !skip {print}
      ' "$rc" >"$tmp"
      mv "$tmp" "$rc"
    fi
    printf '%s\n' "$block" >>"$rc"
    wired+=("$rc")
  done
  log "Aliases wired into: ${wired[*]} (run: source ${wired[0]})"
}

install_aliases

# ---------------------------------------------------------------------------
# 9) Start Tomcat
# ---------------------------------------------------------------------------
start_tomcat() {
  if [[ "$NO_START" -eq 1 ]]; then
    log "Skipping Tomcat start (--no-start)"
    return
  fi
  export JAVA_HOME
  log "Starting Tomcat…"
  "$CATALINA_HOME/bin/startup.sh"
  local login_url="http://localhost:${IIQ_HTTP_PORT}/identityiq/login.jsf"
  if wait_http "$login_url" 300; then
    log "IdentityIQ is up"
  else
    warn "Timed out waiting for $login_url — check $CATALINA_HOME/logs/catalina.out"
    warn "Last 40 log lines:"
    tail -n 40 "$CATALINA_HOME/logs/catalina.out" || true
    exit 1
  fi
}

start_tomcat

cat <<EOF

============================================
 IdentityIQ lab setup complete
============================================
 URL:      http://localhost:${IIQ_HTTP_PORT}/identityiq
 User:     ${IIQ_ADMIN_USER}
 Password: ${IIQ_ADMIN_PASS}
 IIQ home: $IIQ_HOME
 Lab data: $IIQ_LAB_DATA
 Env file: $IIQ_LAB_ENV_FILE
 Log:      $SETUP_LOG

 Handy aliases (after: source ~/.zshrc)
   iiq-start   iiq-stop   iiq-restart
   iiq-logs    iiq-console   iiq-status
   iiq-open    iiq-env

 Teardown:
   ./tools/lab/teardown-local.sh
============================================
EOF
