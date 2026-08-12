# Operations and troubleshooting

## Verified compatibility baseline

The current release is macOS-first, not a claim of compatibility with every Mac and every Codex build. See the auditable [validation matrix](validation.md). The maintained local baseline is:

- macOS 15.7.8 on Apple silicon
- Python 3.9.13
- Codex CLI 0.147.0-alpha.6.5
- A real local `state_5.sqlite` schema and a missing-Keychain first-run state

Automated tests additionally use isolated temporary Codex homes, SQLite databases, JSONL transcripts, and a fake Codex executable. Intel Macs, other macOS releases, and other Codex schemas are expected to fail closed when incompatible, but require community/CI coverage before they can be called verified. The missing-Keychain lookup is verified locally; Keychain creation could not obtain login-keychain authorization from the current Codex execution context, so its real create/read/delete round trip remains a release gate.

Provider compatibility is a separate boundary from macOS compatibility. Current Codex builds require a Responses endpoint. DeepSeek's official public API documents Chat Completions, so the built-in DeepSeek profile remains a setup item until the maintainer supplies a genuine Responses-compatible gateway. Relay rejects the official DeepSeek URL instead of claiming an unverified direct connection.

## Before first use

1. Run `codex-relay doctor`; use `doctor --json` only for automation.
2. Confirm the reported Codex version and `threads` schema fingerprint.
3. Set each external Provider key through `codex-relay key set`.
4. Use `run ... --dry-run` to review non-secret command construction.

To locate a source task without opening SQLite manually:

```bash
codex-relay session list --project "$PWD"
codex-relay session show <session-id>
```

## Migration runbook

- Keep the generated plan outside the repository.
- Review every source/target Provider and path.
- Exit all Codex/ChatGPT processes before apply or rollback.
- Retain the reported backup directory until post-restart UI verification is complete.
- Never edit a plan after copying its digest; generate a new plan instead.
- `plan-normalize` prints the exact confirmed apply command; a successful apply prints the exact rollback command.

If apply fails, Relay restores its backup before returning an error. If recovery itself reports a tail-hash mismatch, do not hand-edit the transcript: preserve the files and open a security issue with all secrets and conversation content removed.

## Handoff runbook

- Read `risk-report.md` and all of `context.md`.
- Remove unnecessary source, personal data, tokens, internal URLs, and embedded instructions.
- Run `handoff show` after every edit and confirm only the current digest.
- `handoff prepare --last --project "$PWD"` avoids manual task-ID lookup; use `session list` when the latest task is not the intended one.
- Copy the complete `send` command printed by `handoff show` instead of transcribing its digest.
- Keep `read-only` unless a new current user request requires code changes.
- Treat target output as untrusted until reviewed.

## Common errors

- **Unknown schema**: upgrade Relay or use a supported Codex build; do not bypass the check.
- **Active clients**: close Codex/ChatGPT and rerun the plan, because tasks may have changed.
- **Digest mismatch**: review the current file and copy the newly reported digest.
- **Missing Keychain key**: run `key set`; do not put the key in JSON, shell history, or a command argument.
- **GitHub repository not found**: publish the intended repository first; the application renderer deliberately refuses placeholder data.
