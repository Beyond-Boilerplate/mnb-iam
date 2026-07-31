# Teller blackbox evaluation

Agentic eval for Meridian Teller: **utterance → `POST /api/chat` → assert on reply + tool steps**.

This is intentionally blackbox (no peeking at MCP internals beyond what Teller returns in `steps`).

## Quick start

```bash
# Stack up with OpenRouter key on iiq-chat
export OPENROUTER_API_KEY=sk-or-…
./tools/lab/docker/up.sh

# List golden cases
python3 tools/iiq-chat/eval/runner.py --list

# Smoke (few cases, slower delay for free-tier LLM)
./tools/iiq-chat/scripts/run_teller_eval.sh --tier smoke --delay 12

# Core suite (default), read-only (no mutate writes)
./tools/iiq-chat/scripts/run_teller_eval.sh --tier core --read-only --delay 10

# Full + known failures (xfail tracked)
./tools/iiq-chat/scripts/run_teller_eval.sh --tier full --delay 12 --jitter 3 --save-raw
```

Reports land in `tools/iiq-chat/eval/reports/`:

- `latest.html` — open in a browser
- `latest.json` — machine-readable
- `raw/<case-id>.json` — with `--save-raw`

## Case schema

```json
{
  "id": "unique-id",
  "tier": "smoke|core|full|stress",
  "tags": ["identity", "read"],
  "mutate": false,
  "query": "Natural language asked to Teller",
  "xfail": false,
  "xfail_reason": "optional",
  "expect": {
    "http_ok": true,
    "min_tools": 1,
    "tools_any_of": ["search_identities"],
    "tools_all_of": [],
    "tools_forbidden": [],
    "require_ok_tools_any_of": ["search_identities"],
    "reply_contains_any": ["Anita"],
    "reply_not_contains_any": ["Invalid filter"],
    "reply_regex": "\\d+",
    "no_tool_errors": true,
    "forbidden_step_substrings": ["invalid filter"],
    "allow_step_substrings": ["405"]
  }
}
```

`require_ok_tools_any_of` + `no_tool_errors` scopes error checks to the primary tools (incidental 404s from exploratory calls won't fail the case).

Use `pass_if_any: [ expect, expect, … ]` for OR success modes (agent may take different valid tool paths).

## Rate limits

Free OpenRouter models throttle easily. Defaults:

| Flag | Default | Purpose |
| --- | --- | --- |
| `--delay` | `10` | Seconds between cases |
| `--jitter` | `2` | Extra `0..jitter` random wait |
| `--timeout` | `180` | Per-chat HTTP timeout |
| `--limit N` | all | Cap case count while iterating |

Bump delay to `15–20` if you see 429 / empty model responses.

## Regression xfails (sample failures that motivated this suite)

| Case | Symptom |
| --- | --- |
| `jml-joiner-dry-run-new` | Joiner dry-run for `joiner.temp` fails because cube must exist first |
| `access-grant-wire-initiator` | `search_entitlements` SCIM `displayName` filter → 400 |
| `cert-create-from-template` | Agent asks for template name instead of discovering / defaulting |

When a fix lands, remove `xfail` (or run with `--strict-xpass` to catch unexpected passes).

## Unit tests (no LLM)

```bash
python3 -m pytest tools/iiq-chat/tests/test_eval_assert.py -q
```
