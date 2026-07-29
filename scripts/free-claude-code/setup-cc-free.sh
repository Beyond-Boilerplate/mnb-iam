from pathlib import Path

script = r'''#!/usr/bin/env bash
#
# Claude Code + CCR + OpenRouter Free Models — macOS bootstrap
#
# What this script does:
#   1. Installs Homebrew when needed.
#   2. Installs Node.js 22+, Claude Code, and Claude Code Router (CCR).
#   3. Prompts once for an OpenRouter API key and validates it.
#   4. Stores secrets in macOS Keychain, not in shell startup files.
#   5. Discovers current free OpenRouter models that support tool calling.
#   6. Builds a fresh CCR config entirely from the CLI/config files.
#   7. Configures Claude Code to use the local CCR gateway.
#   8. Adds an interactive zsh alias: cc
#
# Safe reruns:
#   Existing CCR configuration and Claude settings are backed up first.
#
# Usage:
#   bash setup-claude-code-openrouter-free-macos.sh
#
# Optional:
#   CCR_DEFAULT_MODEL='provider/model:free' bash setup-claude-code-openrouter-free-macos.sh
#
set -Eeuo pipefail
IFS=$'\n\t'
umask 077

SCRIPT_NAME="$(basename "$0")"
CCR_DIR="${HOME}/.claude-code-router"
CLAUDE_DIR="${HOME}/.claude"
LOCAL_BIN="${HOME}/.local/bin"
BACKUP_ROOT="${HOME}/.ccr-setup-backups"
ZSHRC="${HOME}/.zshrc"

OPENROUTER_KEYCHAIN_SERVICE="claude-code-openrouter-api-key"
CCR_KEYCHAIN_SERVICE="claude-code-router-local-client-key"
KEYCHAIN_ACCOUNT="${USER:-$(id -un)}"

CCR_PROVIDER_NAME="OpenRouter"
CCR_GATEWAY_HOST="127.0.0.1"
CCR_GATEWAY_PORT="3456"
CCR_MANAGEMENT_PORT="3458"
CCR_GATEWAY_URL="http://${CCR_GATEWAY_HOST}:${CCR_GATEWAY_PORT}"

PREFERRED_MODEL="${CCR_DEFAULT_MODEL:-cohere/north-mini-code:free}"
RESET_EXISTING=1
BACKUP_DIR=""

BOLD=""
DIM=""
GREEN=""
YELLOW=""
RED=""
RESET=""
if [[ -t 1 ]]; then
  BOLD=$'\033[1m'
  DIM=$'\033[2m'
  GREEN=$'\033[32m'
  YELLOW=$'\033[33m'
  RED=$'\033[31m'
  RESET=$'\033[0m'
fi

info()    { printf '%s\n' "${BOLD}▶${RESET} $*"; }
success() { printf '%s\n' "${GREEN}✓${RESET} $*"; }
warn()    { printf '%s\n' "${YELLOW}!${RESET} $*" >&2; }
die()     { printf '%s\n' "${RED}Error:${RESET} $*" >&2; exit 1; }

on_error() {
  local exit_code=$?
  printf '\n%sSetup stopped at line %s.%s\n' "${RED}" "${BASH_LINENO[0]:-unknown}" "${RESET}" >&2
  if [[ -n "${BACKUP_DIR}" ]]; then
    printf 'Your previous files were backed up at:\n  %s\n' "${BACKUP_DIR}" >&2
  fi
  printf 'Fix the displayed error and rerun:\n  bash %q\n' "$0" >&2
  exit "${exit_code}"
}
trap on_error ERR

usage() {
  cat <<EOF
${SCRIPT_NAME}

Installs and configures Claude Code → CCR → OpenRouter free tool-capable models
on macOS, then creates the interactive zsh alias:

  cc

Usage:
  bash ${SCRIPT_NAME}

Optional default-model override:
  CCR_DEFAULT_MODEL='cohere/north-mini-code:free' bash ${SCRIPT_NAME}

The only required interactive input is your OpenRouter API key when it is not
already stored in macOS Keychain.
EOF
}

case "${1:-}" in
  -h|--help)
    usage
    exit 0
    ;;
  "")
    ;;
  *)
    die "Unknown option: $1. Run with --help."
    ;;
esac

[[ "$(uname -s)" == "Darwin" ]] || die "This installer currently supports macOS only."

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

ensure_path_for_current_script() {
  export PATH="${LOCAL_BIN}:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:${PATH}"
}

ensure_path_for_current_script

print_intro() {
  cat <<EOF

${BOLD}Claude Code + CCR + OpenRouter Free Setup${RESET}

This installer will:
  • install/update the required command-line tools
  • ask you to paste one OpenRouter API key (input is hidden)
  • discover free models that currently support tools
  • keep OpenRouter and CCR keys in macOS Keychain
  • configure a local-only gateway at ${CCR_GATEWAY_URL}
  • add the interactive command: ${BOLD}cc${RESET}

Existing CCR configuration will be backed up before replacement.
EOF
}

ensure_command_line_tools() {
  if xcode-select -p >/dev/null 2>&1; then
    success "Apple Command Line Tools are available"
    return
  fi

  info "Requesting Apple Command Line Tools"
  xcode-select --install >/dev/null 2>&1 || true
  cat <<'EOF'

macOS opened the Command Line Tools installer.
Complete that Apple dialog, then rerun this script.
EOF
  exit 0
}

load_homebrew_shellenv() {
  if [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [[ -x /usr/local/bin/brew ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi
}

install_homebrew() {
  load_homebrew_shellenv
  if command_exists brew; then
    success "Homebrew is available"
    return
  fi

  info "Installing Homebrew"
  NONINTERACTIVE=1 /bin/bash -c \
    "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  load_homebrew_shellenv
  command_exists brew || die "Homebrew installation completed but brew is not on PATH."
  success "Homebrew installed"
}

node_major_version() {
  if ! command_exists node; then
    printf '0\n'
    return
  fi
  node -p 'Number(process.versions.node.split(".")[0])' 2>/dev/null || printf '0\n'
}

install_runtime_dependencies() {
  local node_major
  node_major="$(node_major_version)"

  if (( node_major < 22 )); then
    info "Installing Node.js 22"
    if brew list --versions node@22 >/dev/null 2>&1; then
      brew upgrade node@22 || true
    else
      brew install node@22
    fi
    brew link --overwrite --force node@22
    hash -r
  fi

  if ! command_exists python3; then
    info "Installing Python 3"
    brew install python
    hash -r
  fi

  command_exists node || die "Node.js is not available after installation."
  command_exists npm || die "npm is not available after installation."
  command_exists python3 || die "Python 3 is not available after installation."

  node_major="$(node_major_version)"
  (( node_major >= 22 )) || die "CCR requires Node.js 22 or newer; found $(node --version)."

  success "Node $(node --version), npm $(npm --version), and Python $(python3 --version 2>&1 | awk '{print $2}') are available"
}

install_claude_code() {
  info "Installing or updating Claude Code"
  curl -fsSL https://claude.ai/install.sh | bash
  ensure_path_for_current_script
  command_exists claude || die "Claude Code installed, but the claude command was not found."
  success "Claude Code $(claude --version 2>/dev/null | head -1) is installed"
}

install_ccr() {
  info "Installing or updating Claude Code Router"
  npm install -g @musistudio/claude-code-router@latest
  hash -r
  command_exists ccr || die "CCR installed, but the ccr command was not found."
  success "CCR is installed"
}

read_key_from_keychain() {
  /usr/bin/security find-generic-password \
    -a "${KEYCHAIN_ACCOUNT}" \
    -s "${OPENROUTER_KEYCHAIN_SERVICE}" \
    -w 2>/dev/null || true
}

store_key_in_keychain() {
  local key="$1"
  /usr/bin/security add-generic-password \
    -U \
    -a "${KEYCHAIN_ACCOUNT}" \
    -s "${OPENROUTER_KEYCHAIN_SERVICE}" \
    -w "${key}" >/dev/null
}

prompt_for_openrouter_key() {
  local key=""
  key="$(read_key_from_keychain)"

  if [[ -n "${key}" ]]; then
    success "Found an OpenRouter API key in macOS Keychain"
    printf '%s' "${key}"
    return
  fi

  cat <<'EOF'

OpenRouter key setup — the only required manual step:

  1. Your browser will open the OpenRouter API Keys page.
  2. Sign in and create a key named: claude-code-free
  3. Copy the key.
  4. Return here and paste it. The pasted text will stay hidden.

Purchasing at least $10 in OpenRouter credits is handled on OpenRouter's site,
not by this installer.
EOF

  if [[ -t 0 ]]; then
    printf '\nPress Enter to open OpenRouter API Keys...'
    read -r _
  fi
  open "https://openrouter.ai/settings/keys" >/dev/null 2>&1 || true

  while [[ -z "${key}" ]]; do
    printf '\nPaste your OpenRouter key: '
    IFS= read -r -s key
    printf '\n'
    key="${key//$'\r'/}"
    [[ -n "${key}" ]] || warn "No key was entered. Try again."
  done

  printf '%s' "${key}"
}

validate_openrouter_key() {
  local key="$1"
  local response_file http_code error_message
  response_file="$(mktemp)"

  info "Validating the OpenRouter key"
  http_code="$(
    curl -sS \
      -o "${response_file}" \
      -w '%{http_code}' \
      "https://openrouter.ai/api/v1/chat/completions" \
      -H "Authorization: Bearer ${key}" \
      -H "Content-Type: application/json" \
      -d '{
        "model": "openrouter/free",
        "messages": [
          {"role": "user", "content": "Reply with OK."}
        ],
        "max_tokens": 64
      }'
  )"

  if [[ "${http_code}" != "200" ]]; then
    error_message="$(
      python3 - "${response_file}" <<'PY' 2>/dev/null || true
import json
import sys
try:
    data = json.load(open(sys.argv[1]))
    print(data.get("error", {}).get("message", "Unknown OpenRouter error"))
except Exception:
    pass
PY
    )"
    rm -f "${response_file}"
    die "OpenRouter rejected the key (HTTP ${http_code}): ${error_message:-unknown error}"
  fi

  rm -f "${response_file}"
  success "OpenRouter accepted the key"
}

fetch_free_tool_models() {
  local key="$1"
  local raw_file="$2"
  local output_json="$3"
  local output_txt="$4"

  info "Discovering current free OpenRouter models with tool support"
  curl -fsS \
    "https://openrouter.ai/api/v1/models?supported_parameters=tools&output_modalities=text&sort=coding-high-to-low" \
    -H "Authorization: Bearer ${key}" \
    -o "${raw_file}"

  python3 - "${raw_file}" "${output_json}" "${output_txt}" <<'PY'
import json
import sys
from pathlib import Path

raw_path, json_path, text_path = map(Path, sys.argv[1:4])
payload = json.loads(raw_path.read_text())

models = []
for model in payload.get("data", []):
    model_id = str(model.get("id", "")).strip()
    supported = model.get("supported_parameters") or []
    if model_id.endswith(":free") and "tools" in supported:
        models.append(model_id)

# Preserve API ordering, which was requested with coding-oriented sorting.
models = list(dict.fromkeys(models))

# The dynamic free router is useful as an emergency fallback even though it
# may not appear as a normal model entry in the models endpoint.
if "openrouter/free" in models:
    models.remove("openrouter/free")
models.insert(0, "openrouter/free")

json_path.write_text(json.dumps(models, indent=2) + "\n")
text_path.write_text("\n".join(models) + "\n")

print(len(models))
PY
}

choose_default_model() {
  local models_json="$1"
  local requested="$2"

  python3 - "${models_json}" "${requested}" <<'PY'
import json
import re
import sys

models = json.load(open(sys.argv[1]))
requested = sys.argv[2]

if requested in models:
    print(requested)
    raise SystemExit

# Prefer coding-oriented pinned models over the dynamic router.
coding = [
    m for m in models
    if m != "openrouter/free"
    and re.search(r"(code|coder|devstral)", m, flags=re.I)
]
if coding:
    print(coding[0])
elif len(models) > 1:
    print(models[1])
else:
    print("openrouter/free")
PY
}

backup_existing_configuration() {
  local timestamp
  timestamp="$(date '+%Y%m%d-%H%M%S')"
  BACKUP_DIR="${BACKUP_ROOT}/${timestamp}"
  mkdir -p "${BACKUP_DIR}"

  ccr stop >/dev/null 2>&1 || true

  if [[ -e "${CCR_DIR}" ]]; then
    info "Backing up existing CCR configuration"
    cp -R "${CCR_DIR}" "${BACKUP_DIR}/claude-code-router"
  fi

  if [[ -e "${CLAUDE_DIR}/settings.json" ]]; then
    mkdir -p "${BACKUP_DIR}/claude"
    cp "${CLAUDE_DIR}/settings.json" "${BACKUP_DIR}/claude/settings.json"
  fi

  success "Backup location: ${BACKUP_DIR}"
}

create_fresh_ccr_configuration() {
  local models_json="$1"
  local default_model="$2"
  local local_key="$3"

  rm -rf "${CCR_DIR}"
  mkdir -p "${CCR_DIR}"

  cp "${models_json}" "${CCR_DIR}/openrouter-free-tool-models.json"
  python3 - "${models_json}" "${CCR_DIR}/openrouter-free-tool-models.txt" <<'PY'
import json
import sys
models = json.load(open(sys.argv[1]))
open(sys.argv[2], "w").write("\n".join(models) + "\n")
PY
  printf '%s\n' "${default_model}" > "${CCR_DIR}/default-model"

  python3 - \
    "${models_json}" \
    "${CCR_DIR}/config.json" \
    "${default_model}" \
    "${local_key}" \
    "${CCR_PROVIDER_NAME}" \
    "${CCR_GATEWAY_HOST}" \
    "${CCR_GATEWAY_PORT}" <<'PY'
import json
import sys

models_path, config_path, default_model, local_key, provider_name, host, port = sys.argv[1:8]
models = json.load(open(models_path))

config = {
    "HOST": host,
    "PORT": int(port),
    "APIKEY": local_key,
    "LOG": True,
    "LOG_LEVEL": "info",
    "API_TIMEOUT_MS": 600000,
    "NON_INTERACTIVE_MODE": False,
    "Providers": [
        {
            "name": provider_name,
            "api_base_url": "https://openrouter.ai/api/v1/chat/completions",
            "api_key": "$OPENROUTER_API_KEY",
            "models": models,
            "transformer": {
                "use": ["openrouter"]
            }
        }
    ],
    "Router": {
        "default": f"{provider_name},{default_model}",
        "background": f"{provider_name},{default_model}",
        "think": f"{provider_name},{default_model}",
        "longContext": f"{provider_name},{default_model}"
    }
}

with open(config_path, "w") as fh:
    json.dump(config, fh, indent=2)
    fh.write("\n")
PY

  chmod 600 "${CCR_DIR}/config.json" "${CCR_DIR}/default-model"
  success "Generated CCR configuration with $(python3 -c 'import json,sys; print(len(json.load(open(sys.argv[1]))))' "${models_json}") selectable models"
}

store_local_ccr_key() {
  local key="$1"
  /usr/bin/security add-generic-password \
    -U \
    -a "${KEYCHAIN_ACCOUNT}" \
    -s "${CCR_KEYCHAIN_SERVICE}" \
    -w "${key}" >/dev/null
}

create_api_key_helper() {
  local helper="${LOCAL_BIN}/ccr-local-api-key"
  mkdir -p "${LOCAL_BIN}"

  cat > "${helper}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec /usr/bin/security find-generic-password \\
  -a '${KEYCHAIN_ACCOUNT}' \\
  -s '${CCR_KEYCHAIN_SERVICE}' \\
  -w
EOF
  chmod 700 "${helper}"
}

merge_claude_settings() {
  local default_model="$1"
  local helper="${LOCAL_BIN}/ccr-local-api-key"
  local settings="${CLAUDE_DIR}/settings.json"

  mkdir -p "${CLAUDE_DIR}"

  python3 - \
    "${settings}" \
    "${helper}" \
    "${CCR_GATEWAY_URL}" \
    "${CCR_PROVIDER_NAME}/${default_model}" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
helper = sys.argv[2]
gateway = sys.argv[3]
qualified_model = sys.argv[4]

data = {}
if settings_path.exists():
    try:
        parsed = json.loads(settings_path.read_text())
        if isinstance(parsed, dict):
            data = parsed
    except Exception:
        # The original file was already backed up by the installer.
        data = {}

env = data.get("env")
if not isinstance(env, dict):
    env = {}

# Remove credentials that could override the Keychain helper.
for key in (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "CLAUDE_CODE_OAUTH_TOKEN",
):
    env.pop(key, None)

env.update({
    "CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY": "1",
    "CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS": "1",
    "ANTHROPIC_BASE_URL": gateway,
    "ANTHROPIC_API_BASE_URL": gateway,
    "CLAUDE_AGENT_API_BASE_URL": gateway,
    "ANTHROPIC_MODEL": qualified_model,
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": qualified_model,
    "ANTHROPIC_DEFAULT_SONNET_MODEL": qualified_model,
    "ANTHROPIC_DEFAULT_OPUS_MODEL": qualified_model,
    "CCR_CLAUDE_CODE_MODEL": qualified_model,
    "CODEXL_CLAUDE_CODE_MODEL": qualified_model,
})

data["apiKeyHelper"] = helper
data["env"] = env

settings_path.write_text(json.dumps(data, indent=2) + "\n")
PY

  chmod 600 "${settings}"
  success "Configured Claude Code to use ${CCR_GATEWAY_URL}"
}

create_cc_launcher() {
  local launcher="${LOCAL_BIN}/ccr-claude"
  mkdir -p "${LOCAL_BIN}"

  cat > "${launcher}" <<EOF
#!/usr/bin/env bash
set -Eeuo pipefail

CCR_DIR="\${HOME}/.claude-code-router"
DEFAULT_MODEL_FILE="\${CCR_DIR}/default-model"
OPENROUTER_KEYCHAIN_SERVICE="${OPENROUTER_KEYCHAIN_SERVICE}"
KEYCHAIN_ACCOUNT="${KEYCHAIN_ACCOUNT}"
GATEWAY_URL="${CCR_GATEWAY_URL}"

command -v ccr >/dev/null 2>&1 || {
  echo "CCR is not installed. Rerun ${SCRIPT_NAME}." >&2
  exit 1
}
command -v claude >/dev/null 2>&1 || {
  echo "Claude Code is not installed. Rerun ${SCRIPT_NAME}." >&2
  exit 1
}

openrouter_key="\$(
  /usr/bin/security find-generic-password \\
    -a "\${KEYCHAIN_ACCOUNT}" \\
    -s "\${OPENROUTER_KEYCHAIN_SERVICE}" \\
    -w 2>/dev/null
)" || {
  echo "OpenRouter key was not found in macOS Keychain. Rerun ${SCRIPT_NAME}." >&2
  exit 1
}

# Start or reuse CCR without exposing its management token in the terminal.
start_output_file="\$(mktemp)"
if ! env OPENROUTER_API_KEY="\${openrouter_key}" \\
  ccr start --host "${CCR_GATEWAY_HOST}" --port "${CCR_MANAGEMENT_PORT}" --no-open --gateway \\
  >"\${start_output_file}" 2>&1; then
  cat "\${start_output_file}" >&2
  rm -f "\${start_output_file}"
  exit 1
fi
rm -f "\${start_output_file}"
unset openrouter_key

# Give the gateway a brief moment to become reachable.
for _ in 1 2 3 4 5 6 7 8 9 10; do
  if curl -fsS --max-time 1 "\${GATEWAY_URL}/v1/models" \\
      -H "x-api-key: \$(\"\${HOME}/.local/bin/ccr-local-api-key\")" \\
      >/dev/null 2>&1; then
    break
  fi
  sleep 0.3
done

if ! curl -fsS --max-time 2 "\${GATEWAY_URL}/v1/models" \\
    -H "x-api-key: \$(\"\${HOME}/.local/bin/ccr-local-api-key\")" \\
    >/dev/null 2>&1; then
  echo "CCR started, but the model gateway is not responding at \${GATEWAY_URL}." >&2
  echo "Run: ccr ui" >&2
  exit 1
fi

default_model="\$(cat "\${DEFAULT_MODEL_FILE}")"
qualified_model="${CCR_PROVIDER_NAME}/\${default_model}"

# Prevent an old Claude login/provider environment from outranking CCR.
unset ANTHROPIC_API_KEY
unset ANTHROPIC_AUTH_TOKEN
unset CLAUDE_CODE_OAUTH_TOKEN
unset CLAUDE_CODE_USE_BEDROCK
unset CLAUDE_CODE_USE_VERTEX
unset CLAUDE_CODE_USE_FOUNDRY

export ANTHROPIC_BASE_URL="\${GATEWAY_URL}"
export ANTHROPIC_API_BASE_URL="\${GATEWAY_URL}"
export CLAUDE_AGENT_API_BASE_URL="\${GATEWAY_URL}"
export CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1
export CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1
export ANTHROPIC_MODEL="\${qualified_model}"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="\${qualified_model}"
export ANTHROPIC_DEFAULT_SONNET_MODEL="\${qualified_model}"
export ANTHROPIC_DEFAULT_OPUS_MODEL="\${qualified_model}"
export CCR_CLAUDE_CODE_MODEL="\${qualified_model}"
export CODEXL_CLAUDE_CODE_MODEL="\${qualified_model}"

exec claude "\$@"
EOF

  chmod 700 "${launcher}"
  success "Created the CCR-aware Claude launcher"
}

install_zsh_alias() {
  local marker_start="# >>> claude-code-openrouter-cc >>>"
  local marker_end="# <<< claude-code-openrouter-cc <<<"
  touch "${ZSHRC}"

  python3 - "${ZSHRC}" "${marker_start}" "${marker_end}" "${LOCAL_BIN}" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
start, end, local_bin = sys.argv[2:5]
text = path.read_text() if path.exists() else ""

before = text
while start in text and end in text:
    left, rest = text.split(start, 1)
    _, right = rest.split(end, 1)
    text = left.rstrip() + "\n" + right.lstrip("\n")

block = f"""
{start}
export PATH="{local_bin}:$PATH"
# Interactive alias only: build tools can still use /usr/bin/cc as the C compiler.
alias cc="{local_bin}/ccr-claude"
{end}
"""

text = text.rstrip() + "\n" + block.lstrip()
path.write_text(text)
PY

  success "Added alias: cc"
}

start_ccr_service() {
  local openrouter_key="$1"

  info "Starting CCR and importing the generated configuration"
  env OPENROUTER_API_KEY="${openrouter_key}" \
    ccr start \
      --host "${CCR_GATEWAY_HOST}" \
      --port "${CCR_MANAGEMENT_PORT}" \
      --no-open \
      --gateway >/tmp/ccr-setup-start.log 2>&1 || {
        cat /tmp/ccr-setup-start.log >&2
        die "CCR failed to start."
      }

  local local_key
  local_key="$("${LOCAL_BIN}/ccr-local-api-key")"

  local attempt
  for attempt in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
    if curl -fsS --max-time 2 \
      "${CCR_GATEWAY_URL}/v1/models" \
      -H "x-api-key: ${local_key}" \
      >/dev/null 2>&1; then
      success "CCR gateway is responding at ${CCR_GATEWAY_URL}"
      return
    fi
    sleep 0.4
  done

  cat /tmp/ccr-setup-start.log >&2 || true
  die "CCR started, but its gateway did not become reachable."
}

test_ccr_route() {
  local default_model="$1"
  local response_file
  local http_code
  local local_key

  response_file="$(mktemp)"
  local_key="$("${LOCAL_BIN}/ccr-local-api-key")"

  info "Testing CCR → OpenRouter → ${default_model}"
  http_code="$(
    curl -sS \
      --max-time 90 \
      -o "${response_file}" \
      -w '%{http_code}' \
      "${CCR_GATEWAY_URL}/v1/messages" \
      -H "x-api-key: ${local_key}" \
      -H "anthropic-version: 2023-06-01" \
      -H "content-type: application/json" \
      -d "$(
        python3 - "${CCR_PROVIDER_NAME}/${default_model}" <<'PY'
import json
import sys
print(json.dumps({
    "model": sys.argv[1],
    "max_tokens": 512,
    "messages": [
        {"role": "user", "content": "Reply with exactly: CCR ROUTING WORKS"}
    ]
}))
PY
      )"
  )"

  if [[ "${http_code}" == "200" ]]; then
    rm -f "${response_file}"
    success "End-to-end CCR routing works"
    return
  fi

  warn "The gateway is configured, but the live free-model test returned HTTP ${http_code}."
  warn "Free providers can be temporarily unavailable. The response was:"
  python3 -m json.tool "${response_file}" 2>/dev/null || cat "${response_file}"
  rm -f "${response_file}"
  warn "Setup will finish. Run 'cc' and retry, or select another listed model with /model."
}

print_summary() {
  local model_count="$1"
  local default_model="$2"

  cat <<EOF

${GREEN}${BOLD}Setup complete.${RESET}

Default model:
  ${CCR_PROVIDER_NAME}/${default_model}

Free tool-capable models configured:
  ${model_count}

Launch from a project:
  cd /path/to/project
  cc

Useful commands:
  /model             choose another configured free model inside Claude Code
  /status            confirm Claude Code is using ${CCR_GATEWAY_URL}
  ccr ui             open CCR's optional management/log interface
  ccr stop           stop the background CCR service

Files:
  ${CCR_DIR}/openrouter-free-tool-models.txt
  ${CCR_DIR}/default-model
  ${CLAUDE_DIR}/settings.json

Backup:
  ${BACKUP_DIR}

${YELLOW}Open a new Terminal tab before using cc, or run:${RESET}
  source "${ZSHRC}"

Security note:
  OpenRouter routes prompts and repository context to third-party model
  providers. Use only code and data you are authorized to send externally.
EOF
}

main() {
  local openrouter_key
  local temp_dir
  local raw_models
  local models_json
  local models_txt
  local model_count
  local default_model
  local local_ccr_key

  print_intro
  ensure_command_line_tools
  install_homebrew
  install_runtime_dependencies
  install_claude_code
  install_ccr

  openrouter_key="$(prompt_for_openrouter_key)"
  validate_openrouter_key "${openrouter_key}"
  store_key_in_keychain "${openrouter_key}"
  success "Stored the OpenRouter key in macOS Keychain"

  temp_dir="$(mktemp -d)"
  raw_models="${temp_dir}/openrouter-models-response.json"
  models_json="${temp_dir}/free-tool-models.json"
  models_txt="${temp_dir}/free-tool-models.txt"

  model_count="$(
    fetch_free_tool_models \
      "${openrouter_key}" \
      "${raw_models}" \
      "${models_json}" \
      "${models_txt}"
  )"
  [[ "${model_count}" =~ ^[0-9]+$ ]] || die "Could not determine the discovered model count."
  (( model_count >= 1 )) || die "OpenRouter returned no usable free models."

  default_model="$(choose_default_model "${models_json}" "${PREFERRED_MODEL}")"
  success "Selected default model: ${default_model}"

  backup_existing_configuration

  local_ccr_key="$(openssl rand -hex 32)"
  store_local_ccr_key "${local_ccr_key}"
  create_api_key_helper
  create_fresh_ccr_configuration "${models_json}" "${default_model}" "${local_ccr_key}"
  merge_claude_settings "${default_model}"
  create_cc_launcher
  install_zsh_alias

  start_ccr_service "${openrouter_key}"
  test_ccr_route "${default_model}"

  rm -rf "${temp_dir}"
  unset openrouter_key
  unset local_ccr_key

  print_summary "${model_count}" "${default_model}"
}

main "$@"
'''

path = Path("/mnt/data/setup-claude-code-openrouter-free-macos.sh")
path.write_text(script)
path.chmod(0o755)
print(f"Created {path} ({path.stat().st_size:,} bytes)")
