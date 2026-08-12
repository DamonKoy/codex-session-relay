from __future__ import annotations

import argparse
import datetime as dt
import getpass
import json
import shlex
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import __version__, application, codex, handoff, history, keychain
from .config import (
    add_provider,
    configure_provider,
    get_provider,
    load_config,
    provider_names,
)
from .errors import RelayError


def _print(value: Any) -> None:
    if isinstance(value, (dict, list)):
        print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(value)


def _print_doctor(report: Dict[str, Any]) -> None:
    labels = {
        "platform": "macOS 平台",
        "codex_cli": "Codex CLI",
        "thread_schema": "Codex 任务数据",
        "official_auth_file": "Codex 官方登录",
    }
    print("Codex Session Relay 环境检查\n")
    for check in report["checks"]:
        status = check["status"]
        marker = {"ok": "[通过]", "warning": "[待配置]", "error": "[错误]"}[status]
        name = check["name"]
        label = labels.get(name, name)
        detail = check["detail"]
        if name == "platform":
            detail = "当前系统可用" if status == "ok" else "v0.1.0 仅支持 macOS"
        elif name == "thread_schema" and status == "ok":
            detail = "结构受支持（指纹 %s…）" % detail[:12]
        elif name == "official_auth_file":
            detail = (
                "已检测到官方认证文件（Relay 不读取其内容）"
                if status == "ok"
                else "未检测到认证文件；如需 GPT，请先运行 codex login"
            )
        elif name.startswith("keychain:"):
            provider = name.split(":", 1)[1]
            label = "%s API Key" % provider
            if status == "ok":
                detail = "已安全保存在 macOS 钥匙串"
            elif status == "warning":
                detail = "尚未配置；需要时运行 codex-relay key set %s" % provider
        elif name.startswith("provider_endpoint:"):
            provider = name.split(":", 1)[1]
            label = "%s Responses 接口" % provider
            detail = (
                "尚未配置；运行 codex-relay provider configure %s "
                "--base-url <HTTPS地址>" % provider
            )
        print("%s %s：%s" % (marker, label, detail))
    print()
    if report["ok"]:
        print("环境检查完成：基础功能可用。待配置项不会影响其他 Provider。")
    else:
        print("环境检查未通过：请先处理上面的错误项。")


def _format_time(milliseconds: Any) -> str:
    try:
        value = dt.datetime.fromtimestamp(int(milliseconds) / 1000).astimezone()
        return value.strftime("%Y-%m-%d %H:%M")
    except (TypeError, ValueError, OSError):
        return "未知时间"


def _short_title(value: Any, limit: int = 88) -> str:
    title = " ".join(str(value or "未命名任务").split())
    return title if len(title) <= limit else title[: limit - 1] + "…"


def _print_sessions(rows: List[Dict[str, Any]]) -> None:
    if not rows:
        print("没有找到符合条件的 Codex 任务。")
        return
    print("最近 Codex 任务（复制 ID 可用于 handoff prepare）：\n")
    for row in rows:
        print("- %s  %s" % (row["id"], _short_title(row.get("title"))))
        print(
            "  模型：%s  Provider：%s  更新时间：%s"
            % (
                row.get("model") or "未知",
                row.get("model_provider") or "未知",
                _format_time(row.get("updated_at_ms")),
            )
        )
        print("  项目：%s" % (row.get("cwd") or "未知"))


def _print_history_audit(report: Dict[str, Any]) -> None:
    print("Codex 会话审计（只读）\n")
    print("- 会话文件：%s" % report["session_files"])
    print("- 数据库任务：%s" % report["database_threads"])
    print("- 文件 Provider：%s" % report["file_provider_counts"])
    print("- 数据库 Provider：%s" % report["database_provider_counts"])
    print("- 可归一任务：%s" % report["normalization_candidates"])
    print("- 文件/索引不一致：%s" % len(report["mismatches"]))
    if report["normalization_candidates"]:
        print("\n只有侧边栏任务确实被 Provider 分开时，才需要 plan-normalize。")
    else:
        print("\n当前不需要执行历史归一。")


def _print_plan(plan: Dict[str, Any], path: Path, apply_command: str) -> None:
    print("计划已生成，尚未修改任何 Codex 数据。")
    print("计划文件：%s" % path.resolve())
    print("待处理数量：%s" % len(plan["items"]))
    print("确认摘要：%s" % plan["confirmation_sha256"])
    print("\n审阅计划后执行：\n%s" % apply_command)


def _print_handoff_summary(summary: Dict[str, Any], show_send: bool = False) -> None:
    package = Path(summary["package"])
    print("接力包：%s" % package)
    print("源任务：%s" % summary["source_session_id"])
    print("目标 Provider：%s" % summary["target_provider"])
    print("内容长度：%s 字符" % summary["context_chars"])
    print("当前摘要：%s" % summary["context_sha256"])
    print("疑似 Prompt Injection：%s" % (summary["prompt_injection_findings"] or "未发现"))
    print("默认权限：read-only")
    if show_send:
        command = shlex.join(
            [
                "codex-relay",
                "handoff",
                "send",
                str(package),
                "--confirm",
                summary["context_sha256"],
            ]
        )
        print("\n确认 context.md 已审阅且不含敏感信息后执行：\n%s" % command)
    else:
        print("\n先审阅：%s" % (package / "context.md"))
        print("查看最新摘要：%s" % shlex.join(["codex-relay", "handoff", "show", str(package)]))


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="codex-relay",
        description="Safe provider switching and reviewed cross-model handoffs for Codex.",
    )
    root.add_argument("--version", action="version", version=__version__)
    commands = root.add_subparsers(dest="command", required=True)

    doctor = commands.add_parser("doctor", help="检查 Codex、配置、任务数据库与 Keychain")
    doctor.add_argument("--json", action="store_true", help="输出供脚本读取的 JSON")

    session = commands.add_parser("session", help="列出任务并查找跨模型接力所需的任务 ID")
    session_commands = session.add_subparsers(dest="session_command", required=True)
    session_list = session_commands.add_parser("list", help="列出最近任务")
    session_list.add_argument("--project", type=Path, help="只显示指定项目目录的任务")
    session_list.add_argument("--limit", type=int, default=20, help="最多显示 1-200 条，默认 20")
    session_show = session_commands.add_parser("show", help="显示一个任务")
    session_show.add_argument("session_id", help="任务 ID 或任务名")

    provider = commands.add_parser("provider", help="管理 Provider")
    provider_commands = provider.add_subparsers(dest="provider_command", required=True)
    provider_commands.add_parser("list")
    show = provider_commands.add_parser("show")
    show.add_argument("name")
    add = provider_commands.add_parser("add")
    add.add_argument("name", help="Provider 的本地短名称，例如 example")
    add.add_argument("--display-name", required=True, help="显示名称")
    add.add_argument("--model", required=True, help="Provider 支持的模型 ID")
    add.add_argument("--base-url", required=True, help="Responses-compatible HTTPS 地址")
    add.add_argument("--env-key", default="OPENAI_API_KEY", help="子进程读取 Key 的环境变量名")
    add.add_argument(
        "--allow-insecure-localhost",
        action="store_true",
        help="仅显式允许 localhost 使用 HTTP；不要用于远程地址",
    )
    configure = provider_commands.add_parser(
        "configure", help="为已有 Provider 配置 Responses-compatible 地址"
    )
    configure.add_argument("name")
    configure.add_argument("--base-url", required=True, help="Responses-compatible HTTPS 地址")
    configure.add_argument("--model", default="", help="可选模型覆盖")
    configure.add_argument("--env-key", default="", help="可选环境变量名覆盖")
    configure.add_argument(
        "--allow-insecure-localhost",
        action="store_true",
        help="仅显式允许 localhost 使用 HTTP；不要用于远程地址",
    )

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

    history_parser = commands.add_parser("history", help="审计和安全迁移本地会话")
    history_commands = history_parser.add_subparsers(dest="history_command", required=True)
    history_commands.add_parser("audit")
    plan = history_commands.add_parser("plan-normalize")
    plan.add_argument("--output", type=Path, required=True, help="要生成并人工审阅的 JSON 计划文件")
    plan.add_argument("--target", default="custom", help="目标历史桶；通常保持默认 custom")
    apply = history_commands.add_parser("apply-normalize")
    apply.add_argument("--plan", type=Path, required=True)
    apply.add_argument("--confirm", required=True, help="计划文件中的 confirmation_sha256")
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
    prepare.add_argument("session_id", nargs="?", help="源任务 ID；也可以使用 --last")
    prepare.add_argument("--last", action="store_true", help="使用最近一个任务")
    prepare.add_argument("--project", type=Path, help="与 --last 一起使用，只选择该项目的最近任务")
    prepare.add_argument("--to", required=True, help="目标 Provider，例如 deepseek 或 openai")
    prepare.add_argument("--output", type=Path, help="接力包目录；不填则安全保存在 Relay 数据目录")
    show_package = handoff_commands.add_parser("show")
    show_package.add_argument("package", type=Path)
    send = handoff_commands.add_parser("send")
    send.add_argument("package", type=Path)
    send.add_argument("--confirm", required=True, help="handoff show 显示的当前 context_sha256")
    send.add_argument(
        "--sandbox",
        choices=("read-only", "workspace-write"),
        default="read-only",
        help="默认只读；只有明确需要修改代码时才选择 workspace-write",
    )
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
        _print(report) if args.json else _print_doctor(report)
        return 0 if report["ok"] else 1
    if args.command == "session":
        if args.session_command == "list":
            _print_sessions(codex.list_sessions(args.project, args.limit))
        else:
            _print_sessions([codex.get_session(args.session_id)])
        return 0
    if args.command == "provider":
        if args.provider_command == "list":
            _print(provider_names(config))
        elif args.provider_command == "show":
            _print(get_provider(config, args.name))
        elif args.provider_command == "add":
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
        else:
            updated = configure_provider(
                config,
                args.name,
                args.base_url,
                args.model,
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
            print("%s API Key 已安全写入 macOS 钥匙串。" % args.provider)
        else:
            present = bool(keychain.read_secret(provider["keychain_service"]))
            if present:
                print("%s API Key：已配置（密钥内容不会显示）。" % args.provider)
            else:
                print(
                    "%s API Key：尚未配置。运行 codex-relay key set %s 进行设置。"
                    % (args.provider, args.provider)
                )
        return 0
    if args.command == "run":
        return codex.run_provider(
            config, args.provider, args.model, list(args.codex_args), args.dry_run
        )
    if args.command == "history":
        if args.history_command == "audit":
            _print_history_audit(history.audit())
        elif args.history_command == "plan-normalize":
            plan_value = history.create_normalize_plan(args.output, args.target)
            apply_command = shlex.join(
                [
                    "codex-relay",
                    "history",
                    "apply-normalize",
                    "--plan",
                    str(args.output.resolve()),
                    "--confirm",
                    plan_value["confirmation_sha256"],
                ]
            )
            _print_plan(plan_value, args.output, apply_command)
        elif args.history_command == "apply-normalize":
            result = history.apply_normalize(args.plan, args.confirm)
            print("历史归一完成：%s 个任务。" % result["updated"])
            print("备份目录：%s" % result["backup"])
            print(
                "需要回滚时执行：\n%s"
                % shlex.join(
                    [
                        "codex-relay",
                        "history",
                        "rollback",
                        "--backup",
                        result["backup"],
                        "--confirm",
                        result["rollback_confirmation_sha256"],
                    ]
                )
            )
        elif args.history_command == "rollback":
            result = history.rollback(args.backup, args.confirm)
            print("回滚完成：恢复 %s 个任务。" % result["restored"])
            print("使用的备份：%s" % result["backup"])
        elif args.history_command == "tag-plan":
            plan_value = history.create_tag_plan(args.output, args.remove)
            apply_command = shlex.join(
                [
                    "codex-relay",
                    "history",
                    "tag-apply",
                    "--plan",
                    str(args.output.resolve()),
                    "--confirm",
                    plan_value["confirmation_sha256"],
                ]
            )
            _print_plan(plan_value, args.output, apply_command)
        else:
            result = history.apply_tag_plan(args.plan, args.confirm)
            print("任务标题更新完成：%s 个。" % result["updated"])
            print("数据库备份：%s" % result["backup"])
        return 0
    if args.command == "handoff":
        if args.handoff_command == "prepare":
            if args.last and args.session_id:
                raise RelayError("任务 ID 与 --last 只能选择一个")
            if not args.last and not args.session_id:
                raise RelayError("请提供任务 ID，或使用 --last")
            if args.project and not args.last:
                raise RelayError("--project 只能与 --last 一起使用")
            session_id = (
                codex.latest_session_id(args.project) if args.last else args.session_id
            )
            summary = handoff.prepare(config, session_id, args.to, args.output)
            _print_handoff_summary(summary, show_send=False)
            return 0
        if args.handoff_command == "show":
            _print_handoff_summary(handoff.show(args.package), show_send=True)
            return 0
        return handoff.send(config, args.package, args.confirm, args.sandbox, args.model)
    if args.command == "application":
        _print(application.render(args.repo, args.role, args.output))
        return 0
    raise RelayError("未知命令")


def main(argv: Optional[List[str]] = None) -> int:
    try:
        values = list(sys.argv[1:] if argv is None else argv)
        passthrough: List[str] = []
        if values[:1] == ["run"] and "--" in values:
            boundary = values.index("--")
            passthrough = values[boundary + 1 :]
            values = values[:boundary]
        args = parser().parse_args(values)
        if args.command == "run":
            args.codex_args = passthrough
        return execute(args)
    except RelayError as error:
        print("codex-relay: %s" % error, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("codex-relay: 已取消", file=sys.stderr)
        return 130
