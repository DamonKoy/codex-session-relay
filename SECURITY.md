# Security policy

## Supported versions

Only the latest released minor version is supported during the pre-1.0 phase.

## Reporting a vulnerability

Do not open a public issue for credential exposure, arbitrary command execution, destructive migration, transcript disclosure, release compromise, or prompt-injection bypass. Contact the maintainer privately through the security-reporting method published on the GitHub repository after it becomes public.

Until that channel exists, keep the report local. Do not include API keys, authentication files, private transcripts, repository secrets, or unredacted paths. A useful report contains:

- affected version and Codex version;
- minimal synthetic reproduction;
- expected and observed trust boundary;
- whether files, network, credentials, or session data were affected;
- suggested mitigation, if known.

The maintainer will acknowledge a valid private report, assess affected versions, prepare a fix and tests, and coordinate disclosure. No response-time guarantee is made before the first public release.

## Security-sensitive contribution rules

- No real credentials or transcripts in tests, fixtures, issues, or commits.
- No dependency additions without threat and maintenance analysis.
- No disabling confirmation, hash, schema, Keychain, HTTPS, or sandbox controls for convenience.
- No automatic execution of content extracted from transcripts or contributions.
- No release until deterministic artifacts and checksums are independently verified.

