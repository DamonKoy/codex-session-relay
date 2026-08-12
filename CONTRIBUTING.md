# Contributing

Contributions are welcome after the repository is published.

1. Open an issue describing the user problem and trust-boundary impact.
2. Branch from `main` using the conventions in `docs/git-release.md`.
3. Keep the change minimal and use synthetic fixtures only.
4. Add or update `unittest` coverage.
5. Run:

```bash
PYTHONPATH=src python3 -m compileall -q src tests scripts
PYTHONPATH=src python3 -m unittest discover -v
python3 scripts/build.py
python3 scripts/check_application_lengths.py
```

6. Explain authentication, filesystem, shell, network, database, transcript, and rollback effects in the PR.

By contributing, you agree that your contribution is licensed under Apache-2.0 and that you will follow the Code of Conduct.

Do not submit changes that copy proprietary model output, private transcripts, API credentials, or unlicensed third-party code.

