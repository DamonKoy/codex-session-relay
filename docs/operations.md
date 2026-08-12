# Operations and troubleshooting

## Before first use

1. Run `codex-relay doctor`.
2. Confirm the reported Codex version and `threads` schema fingerprint.
3. Set each external Provider key through `codex-relay key set`.
4. Use `run ... --dry-run` to review non-secret command construction.

## Migration runbook

- Keep the generated plan outside the repository.
- Review every source/target Provider and path.
- Exit all Codex/ChatGPT processes before apply or rollback.
- Retain the reported backup directory until post-restart UI verification is complete.
- Never edit a plan after copying its digest; generate a new plan instead.

If apply fails, Relay restores its backup before returning an error. If recovery itself reports a tail-hash mismatch, do not hand-edit the transcript: preserve the files and open a security issue with all secrets and conversation content removed.

## Handoff runbook

- Read `risk-report.md` and all of `context.md`.
- Remove unnecessary source, personal data, tokens, internal URLs, and embedded instructions.
- Run `handoff show` after every edit and confirm only the current digest.
- Keep `read-only` unless a new current user request requires code changes.
- Treat target output as untrusted until reviewed.

## Common errors

- **Unknown schema**: upgrade Relay or use a supported Codex build; do not bypass the check.
- **Active clients**: close Codex/ChatGPT and rerun the plan, because tasks may have changed.
- **Digest mismatch**: review the current file and copy the newly reported digest.
- **Missing Keychain key**: run `key set`; do not put the key in JSON, shell history, or a command argument.
- **GitHub repository not found**: publish the intended repository first; the application renderer deliberately refuses placeholder data.

