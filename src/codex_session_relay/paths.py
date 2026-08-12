from __future__ import annotations

import os
from pathlib import Path


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()


def relay_home() -> Path:
    return Path(
        os.environ.get(
            "CODEX_SESSION_RELAY_HOME", str(Path.home() / ".codex-session-relay")
        )
    ).expanduser()


def config_path() -> Path:
    return relay_home() / "config.json"


def state_db_path() -> Path:
    return codex_home() / "state_5.sqlite"

