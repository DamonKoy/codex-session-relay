from __future__ import annotations

import argparse
import getpass
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import __version__, application, codex, handoff, history, keychain
from .config import add_provider, get_provider, load_config, provider_names
from .errors import RelayError


def _print(value: Any) -> None:
    if isinstance(value, (dict, list)):
        print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(value)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="codex-relay",
        description="Safe provider switching and reviewed cross-model handoffs for Codex.",
    )
    root.add_argument("--version", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True)

    commands.add_parser("doctor", help="检查 Codex、配置、任务数据库与 Keychain")

    provider = commands.add_parser("provider", help="管理 Provider")
    provider_commands = provider.add_subparsers(dest="provider_command", required=True)
    provider_commands.add_parser("list")
    show = provider_commands.add_parser("show")
    show.add_argument("name")
    add = provider_commands.add_parser("add")
    add.add_argument("name")
    add.add_argument("--display-name", required=True)
    add.add_argument("--model", required=True)
    add.add_argument("--base-url", required=True)
    add.add_argument("--env-key", default="OPENAI_API_KEY")
    add.add_argument("--allow-insecure-localhost", action="store_true")

    key = commands.add_parser("key", help="管理外部 Provider API Key")
    key_commands = key.add_subparsers(dest="key_command", required=True)
    key_set = key_commands.add_parser("set")
    key_set.add_argument("provider")
    key_status = key_commands.add_parser("status")
    key_status.add_argument("provider")

    run = commands.add_parser("run", help="以指定 Provider 启动 Codex")
    run.add_argument("provider")
    run.add_argument("--model")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("codex_args", nargs=argparse.REMAINDER)

    history_parser = commands.add_parser("history", help="审计和安全迁移本地会话")
    history_commands = history_parser.add_subparsers(dest="history_command", required=True)
    history_commands.add_parser("audit")
    plan = history_commands.add_parser("plan-normalize")
    plan.add_argument("--output", type=Path, required=True)
    plan.add_argument("--target", default="custom")
    apply = history_commands.add_parser("apply-normalize")
    apply.add_argument("--plan", type=Path, required=True)
    apply.add_argument("--confirm", required=True)
    rollback = history_commands.add_parser("rollback")
    rollback.add_argument("--backup", type=Path, required=True)
    rollback.add_argument("--confirm", required=True)
    tag_plan = history_commands.add_parser("tag-plan")
    tag_plan.add_argument("--output", type=Path, required=True)
    tag_plan.add_argument("--remove", action="store_true")
    tag_apply = history_commands.add_parser("tag-apply")
    tag_apply.add_argument("--plan", type=Path, required=True)
    tag_apply.add_argument("--confirm", required=True)

    handoff_parser = commands.add_parser("handoff", help="准备、审阅并发送安全接力包")
    handoff_commands = handoff_parser.add_subparsers(dest="handoff_command", required=True)
    prepare = handoff_commands.add_parser("prepare")
    prepare.add_argument("session_id")
    prepare.add_argument("--to", required=True)
    prepare.add_argument("--output", type=Path)
    show_package = handoff_commands.add_parser("show")
    show_package.add_argument("package", type=Path)
    send = handoff_commands.add_parser("send")
    send.add_argument("package", type=Path)
    send.add_argument("--confirm", required=True)
    send.add_argument("--sandbox", choices=("read-only", "workspace-write"), default="read-only")
    send.add_argument("--model")

    application_parser = commands.add_parser("application", help="生成 Codex for Open Source 申请材料")
    application_commands = application_parser.add_subparsers(dest="application_command", required=True)
    render = application_commands.add_parser("render")
    render.add_argument("--repo", required=True)
    render.add_argument(
        "--role",
        choices=("creator", "primary-maintainer", "core-maintainer"),
        required=True,
    )
    render.add_argument("--output", type=Path, default=Path("open-source-application-final.md"))
    return root


def execute(args: argparse.Namespace) -> int:
    config = load_config()
    if args.command == "doctor":
        report = codex.doctor(config)
        _print(report)
        return 0 if report["ok"] else 1
    if args.command == "provider":
        if args.provider_command == "list":
            _print(provider_names(config))
        elif args.provider_command == "show":
            _print(get_provider(config, args.name))
        else:
            updated = add_provider(
                config,
                args.name,
                args.display_name,
                args.model,
                args.base_url,
                args.env_key,
                args.allow_insecure_localhost,
            )
            _print(get_provider(updated, args.name))
        return 0
    if args.command == "key":
        provider = get_provider(config, args.provider)
        if provider["auth_mode"] != "api_key":
            raise RelayError("官方认证 Provider 不接受 Relay 管理的 API Key")
        if args.key_command == "set":
            secret = getpass.getpass("API Key（输入不回显）：")
            keychain.write_secret(provider["keychain_service"], secret)
            _print({"provider": args.provider, "keychain_api_key": "present"})
        else:
            present = bool(keychain.read_secret(provider["keychain_service"]))
            _print({"provider": args.provider, "keychain_api_key": "present" if present else "missing"})
        return 0
    if args.command == "run":
        passthrough = list(args.codex_args)
        if passthrough[:1] == ["--"]:
            passthrough = passthrough[1:]
        return codex.run_provider(config, args.provider, args.model, passthrough, args.dry_run)
    if args.command == "history":
        if args.history_command == "audit":
            _print(history.audit())
        elif args.history_command == "plan-normalize":
            _print(history.create_normalize_plan(args.output, args.target))
        elif args.history_command == "apply-normalize":
            _print(history.apply_normalize(args.plan, args.confirm))
        elif args.history_command == "rollback":
            _print(history.rollback(args.backup, args.confirm))
        elif args.history_command == "tag-plan":
            _print(history.create_tag_plan(args.output, args.remove))
        else:
            _print(history.apply_tag_plan(args.plan, args.confirm))
        return 0
    if args.command == "handoff":
        if args.handoff_command == "prepare":
            _print(handoff.prepare(config, args.session_id, args.to, args.output))
            return 0
        if args.handoff_command == "show":
            _print(handoff.show(args.package))
            return 0
        return handoff.send(config, args.package, args.confirm, args.sandbox, args.model)
    if args.command == "application":
        _print(application.render(args.repo, args.role, args.output))
        return 0
    raise RelayError("未知命令")


def main(argv: Optional[List[str]] = None) -> int:
    try:
        return execute(parser().parse_args(argv))
    except RelayError as error:
        print("codex-relay: %s" % error, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("codex-relay: 已取消", file=sys.stderr)
        return 130

