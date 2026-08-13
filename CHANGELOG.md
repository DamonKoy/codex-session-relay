# Changelog

All notable changes follow Keep a Changelog and Semantic Versioning.

## [Unreleased]

### Added

- Rendered `docs/open-source-application.md` from live GitHub API metrics and switched the copy-paste submission version to descriptive field headings.

## [0.3.0] - 2026-08-13

### Added

- Added direct DeepSeek V4 Flash support through the official Responses API.
- Added a versioned DeepSeek V4 model catalog and a Codex CLI 0.144.0 minimum-version gate.

### Changed

- Simplified first use to ask only for the DeepSeek API key; a separate Responses gateway is no longer required.
- Migrated the v0.2.x pending DeepSeek profile to the official endpoint while preserving explicitly configured custom gateways.
- Kept DeepSeek credentials in macOS Keychain and the child-process environment instead of copying the official documentation's plaintext-token configuration.

## [0.2.1] - 2026-08-12

### Fixed

- Corrected singular and plural GitHub metric wording in generated open-source application text.
- Aligned the default one-line installer with the post-release application and validation documentation fixes.

## [0.2.0] - 2026-08-12

### Added

- Added the `codex-model gpt|deepseek [project]` launch wrapper with Codex argument passthrough.
- Added guided first-run DeepSeek gateway and Keychain setup plus a non-secret status command.
- Added a checksum-verified macOS one-line installer that installs both public commands under `~/.local/bin`.
- Added isolated tests for shortcut routing, first-run failures, project fallback, offline installation, and insecure source rejection.

### Changed

- Added human-readable `doctor` output with `--json` for automation.
- Added recent-task discovery through `session list|show` and `handoff prepare --last`.
- Printed complete next-step commands for handoff, migration, tagging, and rollback.
- Reworked the bilingual quick start around common user goals, PATH setup, troubleshooting, upgrade, and uninstall.
- Require an explicit Responses-compatible gateway for the DeepSeek profile; the official Chat Completions endpoint is no longer treated as a Responses endpoint.
- Exclude local caches, virtual environments, and package metadata from source archives.
- Versioned deterministic artifacts and documentation for the v0.2.0 installation experience.

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
