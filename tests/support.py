from __future__ import annotations

import json
import os
from pathlib import Path

from codex_session_relay.util import sqlite_connection


def make_fake_codex(root: Path, version: str = "0.147.0-test") -> Path:
    binary = root / "codex-bin"
    binary.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--version\" ]; then echo 'codex-cli %s'; exit 0; fi\n"
        "cat >/dev/null\n"
        "exit 0\n" % version,
        encoding="utf-8",
    )
    binary.chmod(0o755)
    return binary


def create_state_db(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite_connection(path) as connection:
        connection.execute(
            """
            CREATE TABLE threads (
                id TEXT PRIMARY KEY,
                name TEXT,
                model_provider TEXT,
                model TEXT,
                title TEXT,
                rollout_path TEXT,
                cwd TEXT,
                git_branch TEXT,
                git_sha TEXT,
                updated_at_ms INTEGER,
                created_at_ms INTEGER
            )
            """
        )
        connection.execute(
            "INSERT INTO threads VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                row["id"],
                row.get("name", row["id"]),
                row.get("model_provider"),
                row.get("model"),
                row.get("title"),
                row.get("rollout_path"),
                row.get("cwd"),
                row.get("git_branch"),
                row.get("git_sha"),
                row.get("updated_at_ms", 1),
                row.get("created_at_ms", 1),
            ),
        )


def create_session(path: Path, session_id: str, provider: str, records=None) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(
            {
                "type": "session_meta",
                "payload": {"id": session_id, "model_provider": provider},
            },
            ensure_ascii=False,
        )
    ]
    lines.extend(records or [])
    data = ("\n".join(lines) + "\n").encode("utf-8")
    path.write_bytes(data)
    return data
