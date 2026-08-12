# Codex Session Relay

Codex Session Relay is a local-first macOS CLI for using Codex official authentication alongside separately authenticated Responses-compatible providers and for creating reviewed, redacted handoff tasks across models.

> **Unofficial project. Not affiliated with OpenAI or DeepSeek.** OpenAI mode uses the existing Codex subscription login. External providers use their own API keys, quotas, and billing. Relay does not transfer subscription quota, read `auth.json` contents, decrypt reasoning, or promise same-thread continuation across providers.

[中文说明](README.zh-CN.md) · [Security model](docs/security-model.md) · [Operations](docs/operations.md) · [Roadmap](docs/roadmap.md)

## Choose your goal

| Goal | Shortest path | Changes history? |
| --- | --- | --- |
| Start Codex with OpenAI | `codex-relay run openai -- -C "$PWD"` | No |
| Route DeepSeek through a Responses gateway | Configure gateway and key, then `run deepseek` | No |
| Handoff the latest task | `prepare --last`, review, `show`, `send` | Creates a new task |
| Repair provider-split sidebar history | `audit`, `plan-normalize`, `apply-normalize` | Yes, with backup and rollback |

You do not need history migration to switch providers or hand off a task.

## Install and check

Requirements: macOS, Python 3.9+, and a previously used Codex CLI/Desktop installation. There are no third-party runtime dependencies.

```bash
cd /path/to/codex-session-relay
python3 -m pip install --user .
codex-relay --version
codex-relay doctor
```

`doctor` reports Passed, Setup needed, or Error. A missing DeepSeek Responses gateway or key is only a setup item and does not block OpenAI. Use `codex-relay doctor --json` for machine-readable output.

If installation succeeds but `codex-relay` is not found, run `python3 -m site --user-base` and add its `bin` directory to `PATH`. You can also build and use the standalone ZipApp:

```bash
python3 scripts/build.py
python3 dist/codex-relay-0.1.0.pyz doctor
(cd dist && shasum -a 256 -c SHA256SUMS)
```

## Run a provider

OpenAI uses existing Codex official authentication; Relay neither reads nor copies its contents:

```bash
codex-relay run openai -- -C "$PWD"
```

Current Codex builds accept the Responses wire API, while DeepSeek's public official API exposes Chat Completions. Do not configure `https://api.deepseek.com` directly. Supply a self-hosted or organizational gateway that explicitly implements `/responses` and routes to DeepSeek:

```bash
codex-relay provider configure deepseek \
  --base-url https://YOUR_RESPONSES_GATEWAY/v1
codex-relay key set deepseek
codex-relay key status deepseek
codex-relay run deepseek -- -C "$PWD"
```

Relay does not provide or operate that gateway. The key is not written to configuration, argv, logs, handoff packages, or Git files. External usage is billed by the configured gateway/provider account. To inspect the non-secret launch command first, add `--dry-run`.

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

- Missing DeepSeek endpoint: ignore it when using only OpenAI, or configure a genuine Responses-compatible gateway; the official Chat Completions URL is rejected.
- Missing external key: follow the gateway's credential requirements and run `key set`.
- Missing official authentication: run `codex login` or sign in through Codex Desktop.
- No task found: run a Codex task first; make sure `--project` matches its working directory.
- Digest mismatch: re-run `handoff show` or regenerate the migration plan; never bypass the check.
- Active client: quit Codex and ChatGPT before migration or rollback.
- Unknown schema: stop and upgrade Relay or report a compatibility issue.

Upgrade with `python3 -m pip install --user --upgrade .` and uninstall with `python3 -m pip uninstall codex-session-relay`. Uninstall intentionally preserves `~/.codex-session-relay` and Keychain items to avoid deleting user data.

See [SECURITY.md](SECURITY.md), [CONTRIBUTING.md](CONTRIBUTING.md), the [architecture](docs/architecture.md), [validation status](docs/validation.md), [operations guide](docs/operations.md), and [Git/release process](docs/git-release.md). Apache-2.0; see [LICENSE](LICENSE).
