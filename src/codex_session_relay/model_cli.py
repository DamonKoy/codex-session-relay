from __future__ import annotations

import argparse
import getpass
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import __version__, codex, keychain
from .config import get_provider, load_config
from .errors import RelayError
from .paths import codex_home


MODEL_ALIASES = {"gpt": "openai", "openai": "openai", "deepseek": "deepseek"}


def _resolve_project(raw: Optional[str]) -> Path:
    if raw is None:
        return Path.cwd().resolve()
    candidate = Path(raw).expanduser()
    try:
        resolved = candidate.resolve(strict=True)
    except (FileNotFoundError, OSError):
        resolved = None
    if resolved is None or not resolved.is_dir():
        current = Path.cwd().resolve()
        print(
            "提示：项目路径无效（%s），改用当前目录：%s" % (candidate, current),
            file=sys.stderr,
        )
        return current
    return resolved


def _setup_deepseek(config: Dict[str, Any]) -> Dict[str, Any]:
    provider = get_provider(config, "deepseek")
    changed = False
    if not keychain.read_secret(provider["keychain_service"]):
        if not sys.stdin.isatty():
            raise RelayError(
                "DeepSeek API Key 尚未配置。请在交互式终端运行 codex-model setup deepseek"
            )
        print("首次配置 DeepSeek V4 Flash（官方 Responses API）")
        secret = getpass.getpass("DeepSeek API Key（输入不回显）：")
        keychain.write_secret(provider["keychain_service"], secret)
        changed = True
    if changed:
        print("DeepSeek 已配置：使用官方 Responses API，密钥保存在 macOS Keychain。")
    return config


def _print_status(config: Dict[str, Any]) -> None:
    result: Dict[str, Any] = {
        "gpt": {
            "provider": "openai",
            "authentication": "Codex official authentication",
            "ready": (codex_home() / "auth.json").exists(),
        }
    }
    provider = get_provider(config, "deepseek")
    endpoint_ready = bool(provider.get("base_url"))
    try:
        key_ready = bool(keychain.read_secret(provider["keychain_service"]))
        key_status = "configured" if key_ready else "missing"
    except RelayError as error:
        key_ready = False
        key_status = "error: %s" % error
    result["deepseek"] = {
        "provider": "deepseek",
        "model": provider["model"],
        "responses_endpoint": provider.get("base_url") or "missing",
        "api_key": key_status,
        "ready": endpoint_ready and key_ready,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="codex-model",
        description="用一个短命令选择 Provider 并在当前项目启动 Codex。",
        epilog=(
            "示例：codex-model gpt | codex-model deepseek | "
            "codex-model deepseek /path/to/project -- --sandbox read-only"
        ),
    )
    root.add_argument("--version", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True)

    for command in ("gpt", "openai", "deepseek"):
        launch = commands.add_parser(command, help="使用 %s 启动 Codex" % command)
        launch.add_argument("project", nargs="?", help="项目目录；默认当前目录")
        launch.add_argument("--model", help="临时覆盖此 Provider 的模型 ID")
        launch.add_argument("--dry-run", action="store_true", help="只显示非秘密启动信息")

    commands.add_parser("status", help="显示两个模式的配置状态，不显示密钥")
    setup = commands.add_parser("setup", help="交互式配置外部 Provider")
    setup.add_argument("provider", choices=("deepseek",))
    return root


def execute(args: argparse.Namespace, passthrough: List[str]) -> int:
    config = load_config()
    if args.command == "status":
        _print_status(config)
        return 0
    if args.command == "setup":
        _setup_deepseek(config)
        return 0

    provider = MODEL_ALIASES[args.command]
    if provider == "deepseek":
        config = _setup_deepseek(config)
    project = _resolve_project(args.project)
    codex_args = ["-C", str(project)] + passthrough
    return codex.run_provider(config, provider, args.model, codex_args, args.dry_run)


def main(argv: Optional[List[str]] = None) -> int:
    try:
        values = list(sys.argv[1:] if argv is None else argv)
        passthrough: List[str] = []
        if "--" in values:
            boundary = values.index("--")
            passthrough = values[boundary + 1 :]
            values = values[:boundary]
        args = parser().parse_args(values)
        return execute(args, passthrough)
    except RelayError as error:
        print("codex-model: %s" % error, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("codex-model: 已取消", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
