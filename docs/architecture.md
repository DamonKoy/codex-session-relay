# Architecture

## Components

```text
codex-relay CLI
├── provider config (~/.codex-session-relay/config.json, 0600)
├── macOS Keychain (external-provider secrets)
├── Codex launcher (official auth or external runtime overrides)
├── history engine (JSONL + state_5.sqlite)
├── handoff engine (reviewable package + stdin send)
└── application renderer (public GitHub API)
```

The package exposes only the `codex-relay` command as a stable v0.1 interface. Python modules are internal and may change before v1.0.

## Provider data flow

OpenAI uses Codex's existing official authentication. Relay does not parse, copy, or export the authentication file. External providers reference a Keychain service in configuration. The secret is retrieved immediately before launch and injected only into the child environment.

Both runtime profiles set the local history provider to `custom`; this affects local task grouping, not remote authentication or billing. The actual model remains on each task.

## Migration data flow

1. Audit JSONL first lines and the `threads` index.
2. Create a versioned plan with Codex version, schema fingerprint, hashes, record counts, original Provider, and target Provider.
3. Require exact SHA-256 confirmation and closed Codex clients.
4. Back up SQLite and original first lines.
5. Conditionally update JSONL and SQLite.
6. Verify Provider alignment, record counts, and unchanged JSONL tails.
7. Restore the backup automatically if any step fails.

## Handoff data flow

1. Locate the source task through `state_5.sqlite`.
2. Whitelist only readable `user` and `assistant` messages.
3. Redact likely credentials and mark prompt-injection indicators.
4. Write an editable package with `context.md`, `manifest.json`, and `risk-report.md`.
5. Recompute the digest and rescan the edited context before send.
6. Wrap history as untrusted data and pass it over stdin to a new read-only Codex task.
7. Persist only a metadata mapping, never the prompt or secret.

