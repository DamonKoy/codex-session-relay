# Codex Session Relay

Codex Session Relay is a local-first macOS CLI for safely using Codex official authentication alongside separately authenticated Responses-compatible model providers. It keeps Relay-created tasks in one local history bucket and creates reviewed, redacted handoff tasks across providers.

> **Unofficial project. Not affiliated with OpenAI or DeepSeek.** A Codex subscription and an external-provider API account remain separate authentication, quota, billing, and trust domains. This project does not transfer subscription quota, decrypt model reasoning, or guarantee same-thread continuation across providers.

[中文说明](README.zh-CN.md) · [Security model](docs/security-model.md) · [Operations](docs/operations.md) · [Roadmap](docs/roadmap.md)

## What it provides

- Provider launch profiles that share the local `custom` history bucket while preserving the real model name.
- Codex official authentication for OpenAI and macOS Keychain-backed API keys for external providers.
- Read-only audits plus SHA-256-confirmed, backed-up, reversible provider normalization and title tagging.
- Two-stage handoff packages containing only readable user/assistant messages, with secret redaction and prompt-injection warnings.
- Read-only target sandboxes by default; `workspace-write` must be selected explicitly.
- A public-GitHub-data renderer for the Codex for Open Source application.

## Requirements

- macOS
- Python 3.9 or newer
- Codex CLI/Desktop with a local `state_5.sqlite` task index
- A valid Codex official login for the OpenAI profile
- A separately funded API key for each external provider

No runtime third-party Python packages are required.

## Install from source

```bash
python3 -m pip install --user .
codex-relay --version
codex-relay doctor
```

Or build and run the standalone ZipApp:

```bash
python3 scripts/build.py
python3 dist/codex-relay-0.1.0.pyz --help
(cd dist && shasum -a 256 -c SHA256SUMS)
```

## Provider workflow

The built-in profiles are `openai` and `deepseek`:

```bash
codex-relay provider list
codex-relay provider show deepseek
codex-relay key set deepseek
codex-relay key status deepseek

# Codex official authentication; no API key is copied by Relay.
codex-relay run openai -- -C "$PWD"

# DeepSeek API key comes from macOS Keychain and is billed by DeepSeek.
codex-relay run deepseek -- -C "$PWD"
```

Add another Responses-compatible provider:

```bash
codex-relay provider add example \
  --display-name "Example Provider" \
  --model example-model \
  --base-url https://api.example.com/v1
codex-relay key set example
```

Remote HTTP URLs are rejected. Local HTTP is available only for `localhost`, `127.0.0.1`, or `::1` with `--allow-insecure-localhost`.

## Safe session normalization

Audit is read-only. Applying changes requires Codex/ChatGPT to be closed and the exact plan digest to be supplied:

```bash
codex-relay history audit
codex-relay history plan-normalize --output /tmp/relay-plan.json
# Review the plan and copy confirmation_sha256 from it.
codex-relay history apply-normalize \
  --plan /tmp/relay-plan.json \
  --confirm <sha256>
```

The command backs up SQLite and every original JSONL first line. It changes only `session_meta.payload.model_provider` and the matching `threads.model_provider`, then verifies the untouched tail of every session.

Rollback uses the backup manifest digest:

```bash
codex-relay history rollback --backup <backup-dir> --confirm <manifest-sha256>
```

Title tags use the same plan/confirm pattern:

```bash
codex-relay history tag-plan --output /tmp/tag-plan.json
codex-relay history tag-apply --plan /tmp/tag-plan.json --confirm <sha256>
# To remove Relay prefixes, create a new plan with --remove.
```

## Safe cross-provider handoff

Handoff never silently resumes an existing cross-provider thread:

```bash
codex-relay handoff prepare <session-id> --to deepseek
codex-relay handoff show <package-dir>
# Review/edit context.md, then copy the current context_sha256.
codex-relay handoff send <package-dir> --confirm <sha256>
```

`prepare` excludes system/developer messages, reasoning, encrypted content, tool calls, and tool outputs. `send` re-scans edited content for secrets, sends it through stdin, creates a new task, and defaults to `--sandbox read-only`.

## Codex for Open Source application

The repository includes a clearly marked pre-publication draft. After the repository is public, generate a final version from live GitHub metrics:

```bash
codex-relay application render \
  --repo DamonKoy/codex-session-relay \
  --role creator \
  --output open-source-application-final.md
```

The renderer refuses a missing/private repository and validates all five English fields against the 500-character limit.

## Trust boundaries

Provider configuration, transcripts, repository content, model output, and third-party contributions are untrusted. See [SECURITY.md](SECURITY.md) and the [security model](docs/security-model.md) before enabling writes.

## License

Apache-2.0. See [LICENSE](LICENSE).
