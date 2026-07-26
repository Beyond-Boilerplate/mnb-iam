#!/usr/bin/env bash
# Greenfield bootstrap for IdentityIQ lab (macOS / Linux / WSL).
# Installs missing package managers + JDK 11 + MySQL 8.4 binaries when needed.
# shellcheck disable=SC2034

detect_os() {
  IIQ_OS="$(uname -s 2>/dev/null || echo unknown)"
  IIQ_ARCH="$(uname -m 2>/dev/null || echo unknown)"
  case "$IIQ_OS" in
    Darwin) IIQ_PLATFORM=macos ;;
    Linux)
      if grep -qi microsoft /proc/version 2>/dev/null; then
        IIQ_PLATFORM=wsl
      else
        IIQ_PLATFORM=linux
      fi
      ;;
    MINGW*|MSYS*|CYGWIN*)
      IIQ_PLATFORM=gitbash
      ;;
    *) IIQ_PLATFORM=unknown ;;
  esac
  export IIQ_OS IIQ_ARCH IIQ_PLATFORM
}

is_linux() { [[ "${IIQ_PLATFORM:-}" == "linux" || "${IIQ_PLATFORM:-}" == "wsl" ]]; }
is_wsl() { [[ "${IIQ_PLATFORM:-}" == "wsl" ]]; }
is_gitbash() { [[ "${IIQ_PLATFORM:-}" == "gitbash" ]]; }

have_sudo() {
  if [[ "$(id -u)" -eq 0 ]]; then
    return 0
  fi
  command -v sudo >/dev/null 2>&1 || return 1
  sudo -n true >/dev/null 2>&1
}

run_root() {
  if [[ "$(id -u)" -eq 0 ]]; then
    "$@"
  else
    sudo "$@"
  fi
}

port_in_use() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1 && return 0
  fi
  if command -v ss >/dev/null 2>&1; then
    ss -ltn "sport = :$port" 2>/dev/null | grep -q ":$port" && return 0
  fi
  if command -v netstat >/dev/null 2>&1; then
    netstat -an 2>/dev/null | grep -E "[.:]${port}[[:space:]].*LISTEN" >/dev/null && return 0
  fi
  # Last resort: try bind via python
  if command -v python3 >/dev/null 2>&1; then
    python3 - "$port" <<'PY' >/dev/null 2>&1
import socket, sys
port=int(sys.argv[1])
s=socket.socket()
try:
    s.bind(("127.0.0.1", port))
except OSError:
    sys.exit(0)  # in use
sys.exit(1)      # free
PY
    return $?
  fi
  return 1
}

ensure_curl() {
  if command -v curl >/dev/null 2>&1; then
    return 0
  fi
  log "Installing curl…"
  if is_macos; then
    die "curl missing on macOS (unexpected). Install Xcode Command Line Tools: xcode-select --install"
  elif is_linux; then
    if command -v apt-get >/dev/null 2>&1; then
      run_root apt-get update -y
      run_root apt-get install -y curl ca-certificates
    elif command -v dnf >/dev/null 2>&1; then
      run_root dnf install -y curl ca-certificates
    elif command -v yum >/dev/null 2>&1; then
      run_root yum install -y curl ca-certificates
    else
      die "curl not found and no supported package manager (apt/dnf/yum)"
    fi
  else
    die "curl is required"
  fi
}

ensure_homebrew() {
  if command -v brew >/dev/null 2>&1; then
    return 0
  fi
  is_macos || return 1
  log "Homebrew not found — installing (NONINTERACTIVE)…"
  ensure_curl
  NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" \
    || die "Homebrew install failed. On a brand-new Mac you may need: xcode-select --install (GUI prompt), then re-run setup."

  # Apple Silicon brew path
  if [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [[ -x /usr/local/bin/brew ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi
  command -v brew >/dev/null 2>&1 || die "brew installed but not on PATH. Open a new terminal or add Homebrew to PATH, then re-run."
  log "Homebrew ready: $(brew --prefix)"
}

linux_pkg_install() {
  local pkgs=("$@")
  if command -v apt-get >/dev/null 2>&1; then
    run_root apt-get update -y
    run_root DEBIAN_FRONTEND=noninteractive apt-get install -y "${pkgs[@]}"
  elif command -v dnf >/dev/null 2>&1; then
    run_root dnf install -y "${pkgs[@]}"
  elif command -v yum >/dev/null 2>&1; then
    run_root yum install -y "${pkgs[@]}"
  else
    return 1
  fi
}

# Map uname arch → Adoptium / MySQL arch tokens
adoptium_os_arch() {
  case "$IIQ_PLATFORM" in
    macos) echo -n "mac" ;;
    linux|wsl) echo -n "linux" ;;
    *) echo -n "linux" ;;
  esac
  echo -n "/"
  case "$IIQ_ARCH" in
    arm64|aarch64) echo "aarch64" ;;
    x86_64|amd64) echo "x64" ;;
    *) die "Unsupported CPU arch: $IIQ_ARCH" ;;
  esac
}

download_file() {
  local url="$1"
  local dest="$2"
  ensure_curl
  log "Downloading $(basename "$dest")…"
  curl -fL --retry 3 --retry-delay 2 -o "$dest" "$url"
}

# Install Temurin JDK 11 into $IIQ_LAB_HOME/jdk if no system JDK 11/17
ensure_java_portable_or_pkg() {
  # Already usable?
  if resolve_java_home_soft; then
    return 0
  fi

  log "No suitable JDK 11/17 found — installing…"

  if is_macos; then
    ensure_homebrew
    brew install openjdk@11 || brew install temurin@11 || true
    if resolve_java_home_soft; then
      return 0
    fi
  elif is_linux; then
    if linux_pkg_install openjdk-11-jdk; then
      if resolve_java_home_soft; then
        return 0
      fi
    fi
  fi

  # Portable Adoptium fallback (no package manager / sudo)
  local os_arch dest tgz
  os_arch="$(adoptium_os_arch)"
  dest="$IIQ_LAB_HOME/jdk"
  tgz="$IIQ_LAB_HOME/temurin11.tar.gz"
  mkdir -p "$IIQ_LAB_HOME"
  local url="https://api.adoptium.net/v3/binary/latest/11/ga/${os_arch}/jdk/hotspot/normal/eclipse?project=jdk"
  download_file "$url" "$tgz"
  rm -rf "$dest"
  mkdir -p "$dest"
  tar -xzf "$tgz" -C "$dest" --strip-components=1
  rm -f "$tgz"
  [[ -x "$dest/bin/java" ]] || die "Portable JDK extract failed at $dest"
  JAVA_HOME="$dest"
  export JAVA_HOME PATH="$JAVA_HOME/bin:$PATH"
  IIQ_INSTALLED_JDK=1
  log "Portable Temurin 11 installed → $JAVA_HOME"
}

# Soft resolve: return 1 instead of die
resolve_java_home_soft() {
  local candidate=""
  if [[ -n "${JAVA_HOME:-}" && -x "${JAVA_HOME}/bin/java" ]]; then
    candidate="$JAVA_HOME"
  elif [[ -x "$IIQ_LAB_HOME/jdk/bin/java" ]]; then
    candidate="$IIQ_LAB_HOME/jdk"
  elif [[ -x /opt/homebrew/opt/openjdk@11/libexec/openjdk.jdk/Contents/Home/bin/java ]]; then
    candidate="/opt/homebrew/opt/openjdk@11/libexec/openjdk.jdk/Contents/Home"
  elif [[ -x /usr/local/opt/openjdk@11/libexec/openjdk.jdk/Contents/Home/bin/java ]]; then
    candidate="/usr/local/opt/openjdk@11/libexec/openjdk.jdk/Contents/Home"
  elif [[ -x /opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin/java ]]; then
    candidate="/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"
  elif [[ -x /usr/lib/jvm/java-11-openjdk-amd64/bin/java ]]; then
    candidate="/usr/lib/jvm/java-11-openjdk-amd64"
  elif [[ -x /usr/lib/jvm/java-11-openjdk-arm64/bin/java ]]; then
    candidate="/usr/lib/jvm/java-11-openjdk-arm64"
  elif [[ -x /usr/lib/jvm/java-17-openjdk-amd64/bin/java ]]; then
    candidate="/usr/lib/jvm/java-17-openjdk-amd64"
  elif command -v /usr/libexec/java_home >/dev/null 2>&1; then
    candidate="$(/usr/libexec/java_home -v 11 2>/dev/null || /usr/libexec/java_home -v 17 2>/dev/null || true)"
  elif command -v java >/dev/null 2>&1; then
    # Derive JAVA_HOME from java binary when possible
    local java_bin
    java_bin="$(command -v java)"
    if command -v readlink >/dev/null 2>&1; then
      java_bin="$(readlink -f "$java_bin" 2>/dev/null || echo "$java_bin")"
    fi
    candidate="$(cd "$(dirname "$java_bin")/.." && pwd)"
  fi

  if [[ -z "$candidate" || ! -x "$candidate/bin/java" ]]; then
    return 1
  fi

  local major
  major="$("$candidate/bin/java" -version 2>&1 | head -1 | sed -E 's/.*version "([0-9]+)(\.[0-9]+)*.*/\1/')"
  if [[ "$major" == "1" ]]; then
    major="$("$candidate/bin/java" -version 2>&1 | head -1 | sed -E 's/.*version "1\.([0-9]+).*/\1/')"
  fi
  if [[ "${major:-0}" -gt 17 ]]; then
    # Too new — keep looking unless this is all we have later
    if [[ -x /opt/homebrew/opt/openjdk@11/libexec/openjdk.jdk/Contents/Home/bin/java ]]; then
      candidate="/opt/homebrew/opt/openjdk@11/libexec/openjdk.jdk/Contents/Home"
    elif [[ -x "$IIQ_LAB_HOME/jdk/bin/java" ]]; then
      candidate="$IIQ_LAB_HOME/jdk"
    else
      warn "Found Java $major at $candidate (IIQ prefers 11/17). Will try to install JDK 11."
      return 1
    fi
  fi

  JAVA_HOME="$candidate"
  export JAVA_HOME PATH="$JAVA_HOME/bin:$PATH"
  log "Using JAVA_HOME=$JAVA_HOME ($("$JAVA_HOME/bin/java" -version 2>&1 | head -1))"
  return 0
}

ensure_base_tools() {
  ensure_curl
  local missing=()
  command -v tar >/dev/null 2>&1 || missing+=(tar)
  command -v gzip >/dev/null 2>&1 || missing+=(gzip)

  if is_macos; then
    # jar comes with JDK; lsof is built-in
    :
  elif is_linux; then
    local need_pkgs=()
    command -v tar >/dev/null 2>&1 || need_pkgs+=(tar)
    command -v gzip >/dev/null 2>&1 || need_pkgs+=(gzip)
    command -v lsof >/dev/null 2>&1 || need_pkgs+=(lsof)
    command -v ss >/dev/null 2>&1 || need_pkgs+=(iproute2)
    if ((${#need_pkgs[@]})); then
      log "Installing base tools: ${need_pkgs[*]}"
      linux_pkg_install "${need_pkgs[@]}" || warn "Could not install some base tools (continuing)"
    fi
  fi
}

# Prefer brew/apt mysql client+server binaries; else download community tarball into lab home
ensure_mysql_binaries() {
  # Already resolved?
  if [[ -n "${IIQ_MYSQL_BIN:-}" && -x "${IIQ_MYSQL_BIN}/mysqld" ]]; then
    return 0
  fi

  if is_macos; then
    ensure_homebrew
    if [[ ! -x /opt/homebrew/opt/mysql@8.4/bin/mysqld && ! -x /usr/local/opt/mysql@8.4/bin/mysqld ]]; then
      log "Installing mysql@8.4 via Homebrew…"
      brew install mysql@8.4
      IIQ_INSTALLED_MYSQL=1
    fi
    if resolve_mysql_bin_dir_soft; then
      return 0
    fi
  elif is_linux; then
    # Prefer package if available, but we still use a lab datadir/port
    if [[ ! -x /usr/sbin/mysqld && ! -x /usr/bin/mysqld ]]; then
      log "Installing MySQL server packages (Linux)…"
      if linux_pkg_install mysql-server mysql-client; then
        IIQ_INSTALLED_MYSQL=1
      elif linux_pkg_install mariadb-server mariadb-client; then
        IIQ_INSTALLED_MYSQL=1
        warn "Using MariaDB packages as MySQL-compatible server"
      else
        warn "Package install failed — trying portable MySQL tarball"
      fi
    fi
    if resolve_mysql_bin_dir_soft; then
      return 0
    fi
  fi

  install_portable_mysql
}

resolve_mysql_bin_dir_soft() {
  if [[ -x /opt/homebrew/opt/mysql@8.4/bin/mysqld ]]; then
    IIQ_MYSQL_BIN="/opt/homebrew/opt/mysql@8.4/bin"
  elif [[ -x /usr/local/opt/mysql@8.4/bin/mysqld ]]; then
    IIQ_MYSQL_BIN="/usr/local/opt/mysql@8.4/bin"
  elif [[ -x "$IIQ_LAB_HOME/mysql/dist/bin/mysqld" ]]; then
    IIQ_MYSQL_BIN="$IIQ_LAB_HOME/mysql/dist/bin"
  elif [[ -x /usr/sbin/mysqld ]]; then
    # Client often in /usr/bin
    IIQ_MYSQL_BIN="/usr/bin"
    export IIQ_MYSQLD_BIN="/usr/sbin/mysqld"
  elif [[ -x /usr/bin/mysqld ]]; then
    IIQ_MYSQL_BIN="/usr/bin"
  else
    return 1
  fi
  export IIQ_MYSQL_BIN PATH="$IIQ_MYSQL_BIN:$PATH"
  return 0
}

install_portable_mysql() {
  local dist="$IIQ_LAB_HOME/mysql/dist"
  if [[ -x "$dist/bin/mysqld" ]]; then
    IIQ_MYSQL_BIN="$dist/bin"
    export IIQ_MYSQL_BIN PATH="$IIQ_MYSQL_BIN:$PATH"
    log "Using portable MySQL at $dist"
    return 0
  fi

  log "Downloading portable MySQL 8.4 into lab home (no system package needed)…"
  mkdir -p "$IIQ_LAB_HOME/mysql"
  local ver="8.4.5"
  local url="" tarball=""

  case "$IIQ_PLATFORM-$IIQ_ARCH" in
    macos-arm64|macos-aarch64)
      tarball="mysql-${ver}-macos14-arm64.tar.gz"
      url="https://cdn.mysql.com/archives/mysql-8.4/${tarball}"
      ;;
    macos-x86_64)
      tarball="mysql-${ver}-macos14-x86_64.tar.gz"
      url="https://cdn.mysql.com/archives/mysql-8.4/${tarball}"
      ;;
    linux-x86_64|wsl-x86_64|linux-amd64|wsl-amd64)
      tarball="mysql-${ver}-linux-glibc2.28-x86_64.tar.xz"
      url="https://cdn.mysql.com/archives/mysql-8.4/${tarball}"
      ;;
    linux-aarch64|wsl-aarch64|linux-arm64|wsl-arm64)
      tarball="mysql-${ver}-linux-glibc2.28-aarch64.tar.xz"
      url="https://cdn.mysql.com/archives/mysql-8.4/${tarball}"
      ;;
    *)
      die "No portable MySQL URL for $IIQ_PLATFORM/$IIQ_ARCH. Install mysql@8.4 (macOS) or mysql-server (Linux) manually."
      ;;
  esac

  local archive="$IIQ_LAB_HOME/mysql/$tarball"
  download_file "$url" "$archive" || die "Failed to download MySQL from $url"

  rm -rf "$dist"
  mkdir -p "$IIQ_LAB_HOME/mysql/extract"
  case "$tarball" in
    *.tar.xz) tar -xJf "$archive" -C "$IIQ_LAB_HOME/mysql/extract" ;;
    *) tar -xzf "$archive" -C "$IIQ_LAB_HOME/mysql/extract" ;;
  esac
  local extracted
  extracted="$(find "$IIQ_LAB_HOME/mysql/extract" -maxdepth 1 -type d -name 'mysql-*' | head -1)"
  [[ -n "$extracted" ]] || die "Could not find extracted MySQL directory"
  mv "$extracted" "$dist"
  rm -rf "$IIQ_LAB_HOME/mysql/extract" "$archive"
  [[ -x "$dist/bin/mysqld" ]] || die "Portable MySQL missing mysqld"
  IIQ_MYSQL_BIN="$dist/bin"
  IIQ_INSTALLED_MYSQL=1
  export IIQ_MYSQL_BIN PATH="$IIQ_MYSQL_BIN:$PATH"
  log "Portable MySQL ready → $IIQ_MYSQL_BIN"
}

mysqld_bin() {
  if [[ -n "${IIQ_MYSQLD_BIN:-}" && -x "$IIQ_MYSQLD_BIN" ]]; then
    printf '%s\n' "$IIQ_MYSQLD_BIN"
  elif [[ -x "${IIQ_MYSQL_BIN}/mysqld" ]]; then
    printf '%s\n' "${IIQ_MYSQL_BIN}/mysqld"
  else
    die "mysqld binary not found"
  fi
}

print_platform_banner() {
  detect_os
  log "Platform: $IIQ_PLATFORM ($IIQ_OS / $IIQ_ARCH)"
  if is_gitbash; then
    cat >&2 <<'EOF'
ERROR: You are running under Git Bash / MSYS on Windows.

Native Windows is supported via PowerShell:

  powershell -ExecutionPolicy Bypass -File .\tools\lab\setup-local.ps1

Or use WSL2 (Ubuntu) and run:

  ./tools/lab/setup-local.sh

EOF
    exit 1
  fi
}

bootstrap_prerequisites() {
  print_platform_banner
  log "Bootstrapping prerequisites for a clean sandbox…"
  ensure_base_tools
  ensure_java_portable_or_pkg
  # jar comes from JDK
  need_cmd jar
  ensure_mysql_binaries
  resolve_mysql_bin_dir_soft || die "MySQL binaries still not available after bootstrap"
  # Replace hard resolve with soft success path
  IIQ_MYSQL_BIN="${IIQ_MYSQL_BIN}"
  export IIQ_MYSQL_BIN
  log "Bootstrap complete (JAVA_HOME=$JAVA_HOME, MYSQL_BIN=$IIQ_MYSQL_BIN)"
}
