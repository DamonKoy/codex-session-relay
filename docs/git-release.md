# Git and release workflow

- Default branch: `main`.
- Feature branches: `feat/<short-name>`, fixes: `fix/<short-name>`, security work: `security/<short-name>`.
- Commits follow Conventional Commits, remain scoped, and contain no generated secrets or real transcripts.
- Every PR must describe trust-boundary changes, tests, migration compatibility, and rollback impact.
- Security-sensitive PRs require explicit maintainer review; automation cannot auto-merge them.
- Versions follow Semantic Versioning. Before v1.0, persisted schema changes still require migration notes.
- Releases require tests, compile checks, deterministic build comparison, checksum verification, secret scanning, changelog updates, and a clean tree.
- Release tags use `vX.Y.Z` and are created only after the release commit is reviewed. This v0.1.0 implementation creates no tag or remote push.

