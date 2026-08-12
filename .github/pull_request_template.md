## Summary

Describe the problem and the smallest change that solves it.

## Security boundaries

- [ ] I considered credentials, transcripts, prompt injection, subprocess arguments/environment, network access, filesystem writes, SQLite/JSONL migration, and release supply chain where relevant.
- [ ] I did not add real credentials, auth files, private transcripts, or personal data.
- [ ] New external endpoints require HTTPS, except explicitly confirmed localhost development paths.

## Validation

List the exact tests and manual checks performed. Use synthetic fixtures only.

## Compatibility and rollback

State supported macOS, Python, and Codex versions affected, plus rollback behavior for persistent-data changes.
