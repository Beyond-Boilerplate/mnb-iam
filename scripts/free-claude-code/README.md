# Claude Code + CCR + OpenRouter Free Models for macOS

A one-command macOS installer for this local routing setup:

```text
Claude Code → Claude Code Router (CCR) → OpenRouter → free tool-capable models
```

The installer is intended for developers who want to learn and use Claude Code with OpenRouter's free model catalog while keeping setup simple and mostly command-line driven.

> **macOS only:** This version supports Apple Silicon and Intel Macs.

**Scripts in this folder:**

| File | Purpose |
| --- | --- |
| `setup-cc-free.sh` | Real installer (bash) |
| `setup-claude-code-openrouter-free-macos.sh` | Thin wrapper that calls `setup-cc-free.sh` |

---

## What the installer does

The script automatically:

- Installs Apple-compatible prerequisites (skipped in `--sandbox` when already on PATH).
- Installs Homebrew when it is not already available (host install only; not in sandbox).
- Installs or updates Node.js 22+, Python 3, Claude Code, and CCR.
- Opens the OpenRouter API-key page (interactive host install only).
- Accepts an OpenRouter key from prompt, `OPENROUTER_API_KEY`, or `OPENROUTER_API_KEY_FILE`.
- Validates the key before continuing.
- Stores secrets in macOS Keychain (or a file keystore under `--sandbox`).
- Discovers the currently available OpenRouter free models that advertise tool support.
- Configures those models in CCR.
- Selects a coding-oriented free model as the initial default when available.
- Configures Claude Code to use the local CCR gateway.
- Creates the `cc` command for launching Claude Code through CCR.
- Starts CCR and runs an end-to-end routing test.
- Backs up an existing CCR configuration before replacing it.

---

## Requirements

- macOS 10.15 or newer.
- An administrator-capable macOS account for installing system prerequisites (host install).
- Internet access.
- An OpenRouter account.
- Terminal access.

You do not need to install Homebrew, Node.js, Python, Claude Code, or CCR beforehand for a normal host install.

---

## Quick start (from this repo)

```bash
cd scripts/free-claude-code
bash setup-cc-free.sh
```

Or:

```bash
bash setup-claude-code-openrouter-free-macos.sh
```

Do not run the entire installer with `sudo`.

Non-interactive key injection:

```bash
OPENROUTER_API_KEY_FILE=/path/to/key \
  bash setup-cc-free.sh
```

---

## Sandbox mode (does not touch your real setup)

Use this to validate the installer without writing your real `~/.zshrc`, macOS Keychain, host CCR config, or ports `3456`/`3458`.

```bash
cd scripts/free-claude-code
OPENROUTER_API_KEY_FILE=/path/to/key \
  bash setup-cc-free.sh --sandbox ./sandbox-run
```

Sandbox behavior:

- Uses an isolated `HOME` under the sandbox directory
- Installs CCR into a sandbox npm prefix (host global npm untouched)
- Stores secrets in `sandbox-run/keystore/` (not Keychain)
- Runs the gateway on `127.0.0.1:13456` and management UI on `:13458`
- Writes `cc` alias only to the sandbox `HOME/.zshrc`

Stop the sandbox CCR when finished:

```bash
HOME="$PWD/sandbox-run/home" PATH="$HOME/.npm-global/bin:$PATH" ccr stop
```

`sandbox-run/` is gitignored.

---

## Download / standalone copy

If you copy the installer elsewhere, take `setup-cc-free.sh` (or the wrapper plus that file). The browser-friendly name is:

```text
setup-claude-code-openrouter-free-macos.sh
```

---

## OpenRouter API-key step

When prompted, the installer will open:

```text
https://openrouter.ai/settings/keys
```

Complete these steps:

1. Sign in to OpenRouter.
2. Create a new API key.
3. Name it something recognizable, such as `claude-code-free`.
4. Copy the key.
5. Return to Terminal.
6. Paste the key and press **Enter**.

Nothing will appear while you paste because the input is intentionally hidden.

The installer validates the key and saves it in macOS Keychain. It does not add the key to `.zshrc` or print it to the terminal.

### Optional OpenRouter credits

OpenRouter currently provides a higher free-model daily request limit after at least **$10 in credits** has been purchased. The installer does not purchase credits or request payment information. Manage credits directly through your OpenRouter account.

Official policy: <https://openrouter.ai/docs/faq>

---

## Apple Command Line Tools prompt

On a new Mac, macOS may display an Apple Command Line Tools installation dialog.

Complete the installation, then rerun:

```bash
cd ~/Downloads
bash setup-claude-code-openrouter-free-macos.sh
```

The installer is designed to be safely rerun.

---

## After installation

Reload your shell configuration:

```bash
source ~/.zshrc
```

Or close Terminal and open a new Terminal window.

Create a project folder:

```bash
mkdir -p ~/code/claude-code-lab
cd ~/code/claude-code-lab
```

Launch Claude Code through CCR:

```bash
cc
```

Always launch it from the project you want Claude Code to work on instead of from your home directory.

---

## Verify routing

Inside Claude Code, enter:

```text
Reply with exactly: CCR ROUTING WORKS
Do not read or modify files.
```

A successful response confirms this route:

```text
Claude Code → local CCR gateway → OpenRouter → selected free model
```

Check the active Claude Code configuration with:

```text
/status
```

---

## Select another free model

Inside Claude Code, run:

```text
/model
```

Choose a model from the displayed picker.

Use the picker rather than manually typing a model identifier. Some model IDs contain multiple separators, including `:free`, and manual values may be interpreted incorrectly by the Claude Code and CCR model-selection layers.

The available list is refreshed each time you rerun the installer.

---

## Choose the initial default model

The installer initially prefers:

```text
cohere/north-mini-code:free
```

If that model is not available in OpenRouter's current free tool-capable catalog, the installer automatically chooses another coding-oriented model.

To request another preferred default, run:

```bash
CCR_DEFAULT_MODEL='provider/model-name:free' \
  bash setup-claude-code-openrouter-free-macos.sh
```

Example:

```bash
CCR_DEFAULT_MODEL='cohere/north-mini-code:free' \
  bash setup-claude-code-openrouter-free-macos.sh
```

The requested model must be present in the free, tool-capable models returned by OpenRouter. Otherwise, the installer chooses an available fallback.

---

## Useful commands

### Launch Claude Code through CCR

```bash
cc
```

Arguments are passed through to Claude Code. For example:

```bash
cc --version
```

### Open the CCR management interface

```bash
ccr ui
```

CCR normally exposes:

```text
Management interface: http://127.0.0.1:3458
Model gateway:       http://127.0.0.1:3456
```

The management URL may include a private access token. Do not share the complete URL.

### Stop CCR

```bash
ccr stop
```

The `cc` launcher starts or reuses CCR automatically the next time it runs.

### View discovered models

```bash
cat ~/.claude-code-router/openrouter-free-tool-models.txt
```

### View the selected default model

```bash
cat ~/.claude-code-router/default-model
```

### Check Claude Code

```bash
claude --version
claude doctor
```

### Check CCR

```bash
ccr --help
```

---

## Files created or updated

### CCR configuration

```text
~/.claude-code-router/
├── config.json
├── config.sqlite                 # may be created when CCR imports the config
├── default-model
├── openrouter-free-tool-models.json
└── openrouter-free-tool-models.txt
```

### Claude Code configuration

```text
~/.claude/settings.json
```

The installer preserves unrelated valid settings where possible and updates the gateway-related values.

### Local launchers

```text
~/.local/bin/ccr-local-api-key
~/.local/bin/ccr-claude
```

### Shell configuration

The installer adds a managed block to:

```text
~/.zshrc
```

The block adds `~/.local/bin` to `PATH` and creates:

```bash
alias cc="$HOME/.local/bin/ccr-claude"
```

### Backups

Before replacing an existing CCR configuration, the installer saves a timestamped backup under:

```text
~/.ccr-setup-backups/YYYYMMDD-HHMMSS/
```

The backup can include:

```text
claude-code-router/
claude/settings.json
```

---

## Credential storage

The installer stores two secrets in macOS Keychain:

| Purpose | Keychain service name |
|---|---|
| OpenRouter API key | `claude-code-openrouter-api-key` |
| Local CCR client key | `claude-code-router-local-client-key` |

The key values are retrieved only when needed by the launcher.

### Replace the OpenRouter key

Delete the saved key:

```bash
security delete-generic-password \
  -a "$USER" \
  -s 'claude-code-openrouter-api-key'
```

Then rerun the installer:

```bash
bash setup-claude-code-openrouter-free-macos.sh
```

### Remove the local CCR key

```bash
security delete-generic-password \
  -a "$USER" \
  -s 'claude-code-router-local-client-key'
```

Rerun the installer afterward to generate a new key.

---

## Rerunning and updating

Rerun the same script to:

- Update Claude Code.
- Update CCR.
- Refresh the current free-model list.
- Recreate the CCR configuration.
- Select a new default model.
- Repair a broken local setup.

Run:

```bash
cd ~/Downloads
bash setup-claude-code-openrouter-free-macos.sh
```

The existing CCR directory and Claude Code settings are backed up first.

The saved OpenRouter key is reused from macOS Keychain, so you normally do not need to paste it again.

---

## Troubleshooting

### `cc: command not found`

Reload the shell configuration:

```bash
source ~/.zshrc
```

Then verify:

```bash
type cc
```

You should see that `cc` is an alias for the CCR-aware launcher.

---

### OpenRouter returns `Missing Authentication header`

The shell variable `$OPENROUTER_API_KEY` is not automatically populated by this installer. That is intentional because the key is stored in macOS Keychain.

To test the stored key without displaying it:

```bash
OPENROUTER_API_KEY="$(security find-generic-password \
  -a "$USER" \
  -s 'claude-code-openrouter-api-key' \
  -w)"

echo "Key length: ${#OPENROUTER_API_KEY}"
unset OPENROUTER_API_KEY
```

A nonzero length confirms that the key exists.

---

### `400 All target providers failed`

Open CCR logs:

```bash
ccr ui
```

Common causes include:

- The selected model is temporarily unavailable.
- The free provider is rate-limited.
- A model was typed manually but is not configured in CCR.
- OpenRouter changed the available free-model catalog.

First try another model inside Claude Code:

```text
/model
```

If models are missing or stale, rerun the installer to refresh the catalog.

---

### `Model "free" is not configured`

This usually occurs when a model ending in `:free` was typed manually with `/model` and the identifier was parsed incorrectly.

Use:

```text
/model
```

Then choose the model from the interactive picker.

---

### CCR gateway is not responding

Stop and restart CCR:

```bash
ccr stop
cc
```

Verify the gateway model endpoint:

```bash
CCR_KEY="$($HOME/.local/bin/ccr-local-api-key)"

curl -sS http://127.0.0.1:3456/v1/models \
  -H "x-api-key: $CCR_KEY" \
  | python3 -m json.tool

unset CCR_KEY
```

---

### OpenRouter key validation fails

Remove the existing Keychain entry:

```bash
security delete-generic-password \
  -a "$USER" \
  -s 'claude-code-openrouter-api-key'
```

Create a new OpenRouter key and rerun the installer.

---

### A free model returns no visible text

Some reasoning models may use most of a small output allowance for internal reasoning. The installer uses a larger allowance for its gateway test, but individual providers can still behave differently.

Choose another free coding model through:

```text
/model
```

---

### Restore a previous configuration

List backups:

```bash
ls -lt ~/.ccr-setup-backups
```

Stop CCR:

```bash
ccr stop
```

Choose the relevant timestamp and restore its CCR directory:

```bash
BACKUP="$HOME/.ccr-setup-backups/YYYYMMDD-HHMMSS"

rm -rf ~/.claude-code-router
cp -R "$BACKUP/claude-code-router" ~/.claude-code-router
```

Restore Claude Code settings when present:

```bash
cp "$BACKUP/claude/settings.json" ~/.claude/settings.json
```

Open a new Terminal and test again.

---

## Remove the setup

Stop CCR:

```bash
ccr stop 2>/dev/null || true
```

Remove the generated launchers and configuration:

```bash
rm -f ~/.local/bin/ccr-claude
rm -f ~/.local/bin/ccr-local-api-key
rm -rf ~/.claude-code-router
```

Remove the managed alias block from `~/.zshrc`, or edit the file manually:

```bash
vim ~/.zshrc
```

Delete the block between:

```text
# >>> claude-code-openrouter-cc >>>
# <<< claude-code-openrouter-cc <<<
```

Remove the Keychain entries:

```bash
security delete-generic-password \
  -a "$USER" \
  -s 'claude-code-openrouter-api-key' 2>/dev/null || true

security delete-generic-password \
  -a "$USER" \
  -s 'claude-code-router-local-client-key' 2>/dev/null || true
```

Optionally uninstall CCR:

```bash
npm uninstall -g @musistudio/claude-code-router
```

Claude Code itself can remain installed and be used independently, or it can be removed according to Anthropic's current uninstall instructions.

---

## Security and privacy

- Do not paste API keys into chat, issue trackers, screenshots, or documentation.
- The complete CCR management URL can contain a private token; do not share it.
- OpenRouter routes prompts and repository context to third-party model providers.
- Use only source code and data you are authorized to send to external providers.
- Do not use employer-owned, client-owned, regulated, or confidential repositories unless your organization has explicitly approved the provider and data-handling path.
- Review OpenRouter's privacy and provider-routing controls before using sensitive projects.
- Free models can change, disappear, become rate-limited, or behave differently over time.

This setup is best treated as a personal learning and experimentation environment until your organization's security, privacy, legal, and engineering requirements have been addressed.

---

## Architecture

```text
┌────────────────────┐
│ Claude Code CLI    │
│ launched with cc   │
└─────────┬──────────┘
          │ Anthropic-compatible requests
          ▼
┌────────────────────────────┐
│ Claude Code Router         │
│ Gateway: 127.0.0.1:3456    │
│ Manager: 127.0.0.1:3458    │
└─────────┬──────────────────┘
          │ OpenAI Chat Completions adapter
          ▼
┌────────────────────┐
│ OpenRouter API     │
└─────────┬──────────┘
          │
          ▼
┌────────────────────────────┐
│ Selected free model/provider│
└────────────────────────────┘
```

---

## Official references

- Claude Code setup: <https://docs.anthropic.com/en/docs/claude-code/getting-started>
- Claude Code CLI reference: <https://docs.anthropic.com/en/docs/claude-code/cli-usage>
- Claude Code Router: <https://github.com/musistudio/claude-code-router>
- OpenRouter free-model router: <https://openrouter.ai/docs/guides/routing/routers/free-router>
- OpenRouter free-model limits: <https://openrouter.ai/docs/faq>

---

## Disclaimer

This is a community setup workflow built around independent third-party tools. Anthropic, OpenRouter, model providers, CCR, and macOS can change their APIs, installation behavior, model availability, or limits. Review the script before running it and rerun it when you need to refresh dependencies or free-model configuration.
