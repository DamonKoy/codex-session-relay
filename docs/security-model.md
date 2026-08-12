# Security model

## Protected assets

- Codex official authentication and external Provider API keys.
- Local source repositories and files reachable by an agent.
- Codex JSONL transcripts, encrypted reasoning, and `state_5.sqlite`.
- Provider endpoints, release artifacts, and contributor trust.

## Threats

- A malicious Provider URL redirects prompts or credentials.
- Historical conversation text contains prompt injection or commands.
- A contributor adds secret logging, unsafe subprocess flags, or destructive migration logic.
- A stale migration plan overwrites concurrently changed tasks.
- A compromised release or dependency changes execution behavior.
- An agent launched with write or network access damages files or exfiltrates data.

## Controls

- HTTPS is mandatory except explicitly confirmed loopback HTTP.
- The built-in DeepSeek endpoint is restricted to the official HTTPS host and uses a versioned V4 model catalog; arbitrary Providers still require explicit Responses-compatible configuration.
- External credentials live in Keychain and never appear in persistent config or command arguments.
- Handoff extraction is an allowlist; system/developer content, reasoning, encrypted content, and tools are excluded.
- Secret patterns are redacted at prepare time and scanned again after editing.
- Historical content is wrapped as untrusted data, and the target defaults to `read-only`.
- Migration uses schema/version binding, content hashes, conditional SQL, an exclusive lock, client-process checks, backups, verification, and automatic recovery.
- Builds use no runtime dependency and deterministic archives with checksums.
- The convenience installer requires HTTPS, verifies the versioned ZipApp checksum before replacement, and preserves a conflicting regular target instead of deleting it.

## Explicit non-goals

- Decrypting or copying encrypted model reasoning.
- Sharing Codex subscription quota with external providers.
- Automatically trusting, sending, executing, merging, or publishing model/contributor output.
- Supporting remote HTTP Provider endpoints.
- Claiming protection against every secret format or prompt-injection technique.
- Treating a checksum hosted beside a release asset as a substitute for signed releases or independent provenance.

Secret scanning is defense in depth, not a guarantee. Users must review every handoff package before supplying its current digest.
