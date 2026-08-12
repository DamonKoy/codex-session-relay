# Changelog

All notable changes follow Keep a Changelog and Semantic Versioning.

## [Unreleased]

### Changed

- Added human-readable `doctor` output with `--json` for automation.
- Added recent-task discovery through `session list|show` and `handoff prepare --last`.
- Printed complete next-step commands for handoff, migration, tagging, and rollback.
- Reworked the bilingual quick start around common user goals, PATH setup, troubleshooting, upgrade, and uninstall.
- Require an explicit Responses-compatible gateway for the DeepSeek profile; the official Chat Completions endpoint is no longer treated as a Responses endpoint.
- Exclude local caches, virtual environments, and package metadata from source archives.

### Fixed

- Treat a missing macOS Keychain item as an expected first-run setup state on current macOS.
- Keep long or multiline Codex task titles readable in session listings.
- Migrate the early draft's invalid direct DeepSeek URL to a safe pending-setup state without changing its Keychain reference.

## [0.1.0] - 2026-08-12

### Added

- macOS Keychain-backed external Provider profiles and Codex official-auth profile.
- Shared local history bucket with real model preservation.
- Read-only history audit, confirmed normalization, backup, verification, rollback, and title tagging.
- Reviewed handoff packages with message allowlisting, secret redaction, prompt-injection warnings, stdin transfer, and read-only default.
- Public GitHub metrics-based Codex for Open Source application renderer.
- Deterministic ZipApp/source builds, checksums, tests, bilingual documentation, and security policy.
