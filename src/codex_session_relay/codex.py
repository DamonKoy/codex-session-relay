from __future__ import annotations

import os
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import keychain
from .config import get_provider
from .errors import RelayError
from .paths import codex_home, state_db_path
from .util import sha256_bytes


REQUIRED_THREAD_COLUMNS = {"id", "model_provider", "model", "title", "rollout_path"}


def binary_path() -> str:
    candidates = [
        os.environ.get("CODEX_CLI_PATH"),
        "/Applications/ChatGPT.app/Contents/Resources/codex",
        shutil.which("codex"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(candidate)
    raise RelayError("找不到 Codex CLI；可通过 CODEX_CLI_PATH 显式指定")


def version() -> str:
    process = subprocess.run(
        [binary_path(), "--version"], capture_output=True, text=True, check=False
    )
    if process.returncode != 0:
        raise RelayError("无法读取 Codex CLI 版本")
    match = re.search(r"codex-cli\s+([^\s]+)", process.stdout)
    return match.group(1) if match else process.stdout.strip()


def thread_schema() -> List[Dict[str, Any]]:
    path = state_db_path()
    if not path.exists():
        raise RelayError("找不到 Codex 任务索引: %s" % path)
    with sqlite3.connect(str(path)) as connection:
        rows = connection.execute("PRAGMA table_info(threads)").fetchall()
    if not rows:
        raise RelayError("Codex 任务索引缺少 threads 表")
    schema = [
        {
            "cid": row[0],
            "name": row[1],
            "type": row[2],
            "notnull": row[3],
            "default": row[4],
            "pk": row[5],
        }
        for row in rows
    ]
    columns = {item["name"] for item in schema}
    missing = sorted(REQUIRED_THREAD_COLUMNS - columns)
    if missing:
        raise RelayError("未知 Codex schema，threads 缺少: %s" % ", ".join(missing))
    return schema


def schema_fingerprint() -> str:
    import json

    return sha256_bytes(
        json.dumps(thread_schema(), sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    )


def active_clients() -> List[str]:
    if os.environ.get("CODEX_SESSION_RELAY_TEST_MODE") == "1":
        return []
    process = subprocess.run(
        [
            "/usr/bin/pgrep",
            "-afil",
            r"/Applications/(ChatGPT|Codex)\.app/Contents/MacOS/|/Contents/Resources/codex( |$)",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return [line for line in process.stdout.splitlines() if "codex-relay" not in line]


def runtime(
    config: Dict[str, Any], provider_name: str, model_override: Optional[str] = None
) -> Tuple[List[str], Dict[str, str], Optional[str]]:
    provider = get_provider(config, provider_name)
    environment = dict(os.environ)
    environment.pop("OPENAI_BASE_URL", None)
    environment.pop("OPENAI_API_BASE", None)
    options = ["-c", 'model_provider="custom"']
    if provider["auth_mode"] == "codex_official":
        environment.pop("OPENAI_API_KEY", None)
        options.extend(
            [
                "-c",
                'model_providers.custom.name="OpenAI"',
                "-c",
                "model_providers.custom.requires_openai_auth=true",
                "-c",
                "model_providers.custom.supports_websockets=true",
                "-c",
                'model_providers.custom.wire_api="responses"',
            ]
        )
        if model_override:
            options.extend(["-m", model_override])
        return options, environment, model_override

    secret = keychain.read_secret(provider["keychain_service"])
    if not secret:
        raise RelayError(
            "Provider %s 尚未配置 API Key；请先运行 codex-relay key set %s"
            % (provider_name, provider_name)
        )
    environment[provider["env_key"]] = secret
    model = model_override or provider["model"]
    options.extend(
        [
            "-m",
            model,
            "-c",
            'model_providers.custom.name=%s' % _toml_string(provider["display_name"]),
            "-c",
            'model_providers.custom.base_url=%s' % _toml_string(provider["base_url"]),
            "-c",
            "model_providers.custom.requires_openai_auth=false",
            "-c",
            "model_providers.custom.supports_websockets=false",
            "-c",
            'model_providers.custom.wire_api="responses"',
            "-c",
            "model_providers.custom.env_key=%s" % _toml_string(provider["env_key"]),
        ]
    )
    return options, environment, model


def _toml_string(value: str) -> str:
    import json

    return json.dumps(value)


def run_provider(
    config: Dict[str, Any],
    provider_name: str,
    model: Optional[str],
    passthrough: List[str],
    dry_run: bool,
) -> int:
    options, environment, target_model = runtime(config, provider_name, model)
    command = [binary_path()] + options + passthrough
    if dry_run:
        import json

        print(
            json.dumps(
                {
                    "provider": provider_name,
                    "model": target_model,
                    "history_model_provider": "custom",
                    "api_key_source": (
                        "Codex official authentication"
                        if get_provider(config, provider_name)["auth_mode"]
                        == "codex_official"
                        else "macOS Keychain"
                    ),
                    "command": command,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    return subprocess.run(command, env=environment, check=False).returncode


def doctor(config: Dict[str, Any]) -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = []
    checks.append(
        {
            "name": "platform",
            "status": "ok" if sys.platform == "darwin" else "error",
            "detail": sys.platform,
        }
    )
    try:
        checks.append({"name": "codex_cli", "status": "ok", "detail": version()})
    except RelayError as error:
        checks.append({"name": "codex_cli", "status": "error", "detail": str(error)})
    try:
        fingerprint = schema_fingerprint()
        checks.append(
            {"name": "thread_schema", "status": "ok", "detail": fingerprint}
        )
    except RelayError as error:
        checks.append(
            {"name": "thread_schema", "status": "error", "detail": str(error)}
        )
    checks.append(
        {
            "name": "official_auth_file",
            "status": "ok" if (codex_home() / "auth.json").exists() else "warning",
            "detail": "present" if (codex_home() / "auth.json").exists() else "missing",
        }
    )
    for name, provider in sorted(config["providers"].items()):
        if provider["auth_mode"] != "api_key":
            continue
        try:
            present = bool(keychain.read_secret(provider["keychain_service"]))
            status = "ok" if present else "warning"
            detail = "present" if present else "missing"
        except RelayError as error:
            status, detail = "error", str(error)
        checks.append(
            {"name": "keychain:%s" % name, "status": status, "detail": detail}
        )
    return {
        "ok": not any(check["status"] == "error" for check in checks),
        "checks": checks,
    }

