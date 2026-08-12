# Codex Session Relay

[![CI](https://github.com/DamonKoy/codex-session-relay/actions/workflows/ci.yml/badge.svg)](https://github.com/DamonKoy/codex-session-relay/actions/workflows/ci.yml)

Codex Session Relay is a local-first macOS CLI for using Codex official authentication alongside separately authenticated Responses-compatible providers and for creating reviewed, redacted handoff tasks across models.

> **Unofficial project. Not affiliated with OpenAI or DeepSeek.** OpenAI mode uses the existing Codex subscription login. External providers use their own API keys, quotas, and billing. Relay does not transfer subscription quota, read `auth.json` contents, decrypt reasoning, or promise same-thread continuation across providers.

## One-minute start

Requirements: macOS, Python 3.9+, and a previously installed or used Codex CLI/Desktop.

```bash
curl -fsSL https://raw.githubusercontent.com/DamonKoy/codex-session-relay/main/install.sh | sh
```

Open a new terminal, enter a project directory, and run:

```bash
codex-model gpt
codex-model deepseek
```

- `gpt` uses existing Codex official authentication without reading or copying `auth.json`.
- The first `deepseek` run stores the DeepSeek API key through a no-echo prompt in macOS Keychain; the official V4 Responses endpoint is built in.
- Select a project with `codex-model gpt /path/to/project`.
- Forward Codex arguments with `codex-model deepseek -- --sandbox read-only`.
- Inspect readiness with `codex-model status`; advanced controls remain under `codex-relay`.

“Switching” selects a Provider for that launch; it does not persistently rewrite `~/.codex/config.toml`. DeepSeek now natively supports the Responses API required by Codex. Relay uses `deepseek-v4-flash` at `https://api.deepseek.com/` and requires Codex CLI 0.144.0 or newer for the official model catalog.

[中文说明](README.zh-CN.md) · [Security model](docs/security-model.md) · [Operations](docs/operations.md) · [Roadmap](docs/roadmap.md)

## Choose your goal

| Goal | Shortest path | Changes history? |
| --- | --- | --- |
| Start Codex with OpenAI | `codex-model gpt` | No |
| Start Codex with DeepSeek V4 Flash | `codex-model deepseek` (Key setup on first run) | No |
| Handoff the latest task | `prepare --last`, review, `show`, `send` | Creates a new task |
| Repair provider-split sidebar history | `audit`, `plan-normalize`, `apply-normalize` | Yes, with backup and rollback |

You do not need history migration to switch providers or hand off a task.

## Manual install and check

Requirements: macOS, Python 3.9+, and a previously used Codex CLI/Desktop installation. There are no third-party runtime dependencies.

```bash
cd /path/to/codex-session-relay
python3 -m pip install --user .
codex-relay --version
codex-relay doctor
```

`doctor` reports Passed, Setup needed, or Error. A missing DeepSeek key is only a setup item and does not block OpenAI. Use `codex-relay doctor --json` for machine-readable output.

If installation succeeds but `codex-relay` is not found, run `python3 -m site --user-base` and add its `bin` directory to `PATH`. You can also build and use the standalone ZipApp:

```bash
python3 scripts/build.py
python3 dist/codex-relay-0.3.0.pyz doctor
(cd dist && shasum -a 256 -c SHA256SUMS)
```

## Use the low-level provider command

OpenAI uses existing Codex official authentication; Relay neither reads nor copies its contents:

```bash
codex-relay run openai -- -C "$PWD"
```

The built-in profile uses DeepSeek's official Responses endpoint and its V4 Flash model catalog:

```bash
codex-relay key set deepseek
codex-relay key status deepseek
codex-relay run deepseek -- -C "$PWD"
```

The key is not written to configuration, argv, logs, handoff packages, or Git files. It is injected only into the child process environment. DeepSeek usage is billed independently by the DeepSeek account. To inspect the non-secret launch command first, add `--dry-run`. Advanced users may still override the built-in profile with `provider configure` for another Responses-compatible gateway.

## Handoff to another model

Use the latest task for the current project:

```bash
codex-relay handoff prepare --last --project "$PWD" --to deepseek
```

Or select an older task:

```bash
codex-relay session list --project "$PWD"
codex-relay handoff prepare <session-id> --to deepseek
```

`prepare` only creates a local package. Review `context.md` and `risk-report.md`, remove anything unnecessary, then run the exact `handoff show` command printed by the CLI. `show` prints the current SHA-256 and a complete copyable `send` command.

`send` re-scans edited content, transfers it through stdin, creates a new task, and defaults to `--sandbox read-only`. It excludes system/developer messages, reasoning, encrypted content, tool calls, and tool output. Historical text is explicitly wrapped as untrusted data.

## Normalize history only when needed

```bash
codex-relay history audit
codex-relay history plan-normalize --output /tmp/relay-plan.json
```

`audit` is read-only. `plan-normalize` changes nothing and prints the full SHA-256-confirmed apply command. Review the plan and quit Codex/ChatGPT before copying that command. A successful apply prints the backup directory and full rollback command.

Relay changes only `session_meta.payload.model_provider` and the matching SQLite index. It verifies unchanged transcript tails and fails closed on active clients, unknown schemas, changed files, locks, or digest mismatches.

## Common issues

- Unsupported Codex version: upgrade to Codex CLI 0.144.0 or newer before using the built-in DeepSeek V4 profile.
- Missing external key: create a DeepSeek API key and run `key set`; Relay never prints its value.
- Missing official authentication: run `codex login` or sign in through Codex Desktop.
- No task found: run a Codex task first; make sure `--project` matches its working directory.
- Digest mismatch: re-run `handoff show` or regenerate the migration plan; never bypass the check.
- Active client: quit Codex and ChatGPT before migration or rollback.
- Unknown schema: stop and upgrade Relay or report a compatibility issue.

Re-run the one-line installer to upgrade to the version declared by the installer. It accepts only HTTPS releases, verifies SHA-256 before replacement, installs to `~/.local/bin`, and updates `~/.zshrc` idempotently. An existing regular file is retained as `.previous`. Source installs can be upgraded with `python3 -m pip install --user --upgrade .` and removed with `python3 -m pip uninstall codex-session-relay`. Uninstall intentionally preserves Relay configuration and Keychain items.

See [SECURITY.md](SECURITY.md), [CONTRIBUTING.md](CONTRIBUTING.md), the [architecture](docs/architecture.md), [validation status](docs/validation.md), [operations guide](docs/operations.md), and [Git/release process](docs/git-release.md). Apache-2.0; see [LICENSE](LICENSE).
