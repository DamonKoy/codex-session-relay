from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    if Path(sys.argv[0]).name == "codex-model":
        from .model_cli import main as model_main

        return model_main()
    from .cli import main as relay_main

    return relay_main()
