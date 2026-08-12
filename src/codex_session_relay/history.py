from __future__ import annotations

import base64
import collections
import json
import os
import re
import shutil
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from . import codex
from .errors import RelayError
from .paths import codex_home, relay_home, state_db_path
from .util import (
    atomic_write_bytes,
    digest_json,
    read_json,
    sha256_bytes,
    sha256_file,
    timestamp,
    utc_now,
    write_json,
)


PROVIDER_PATTERN = re.compile(rb'("model_provider"\s*:\s*)"([^"]+)"')
TAG_PREFIXES = ("[GPT] ", "[DS] ")


def _session_paths() -> List[Path]:
    paths: List[Path] = []
    for directory in (codex_home() / "sessions", codex_home() / "archived_sessions"):
        if directory.exists():
            paths.extend(directory.rglob("*.jsonl"))
    return sorted(paths)


def _read_session(path: Path) -> Dict[str, Any]:
    raw = path.read_bytes()
    first, separator, tail = raw.partition(b"\n")
    try:
        record = json.loads(first.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RelayError("会话首行不是合法 JSON: %s" % path) from error
    if record.get("type") != "session_meta":
        raise RelayError("会话首行不是 session_meta: %s" % path)
    payload = record.get("payload") or {}
    session_id = payload.get("id")
    provider = payload.get("model_provider")
    if not isinstance(session_id, str) or not isinstance(provider, str):
        raise RelayError("会话首行缺少 id/model_provider: %s" % path)
    if len(PROVIDER_PATTERN.findall(first)) != 1:
        raise RelayError("会话首行必须且只能包含一个 model_provider: %s" % path)
    return {
        "id": session_id,
        "path": str(path.resolve()),
        "provider": provider,
        "file_sha256": sha256_bytes(raw),
        "first_line_sha256": sha256_bytes(first),
        "first_line_b64": base64.b64encode(first).decode("ascii"),
        "tail_sha256": sha256_bytes(tail),
        "tail_size": len(tail),
        "record_count": len(raw.splitlines()),
        "had_separator": bool(separator),
    }


def _thread_rows() -> Dict[str, Dict[str, Any]]:
    codex.thread_schema()
    with sqlite3.connect(str(state_db_path())) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT id, model_provider, model, title, rollout_path FROM threads"
        ).fetchall()
    return {row["id"]: dict(row) for row in rows}


def audit() -> Dict[str, Any]:
    sessions = [_read_session(path) for path in _session_paths()]
    rows = _thread_rows()
    file_providers = collections.Counter(item["provider"] for item in sessions)
    db_providers = collections.Counter(
        (item.get("model_provider") or "<unset>") for item in rows.values()
    )
    models = collections.Counter((item.get("model") or "<unset>") for item in rows.values())
    mismatches = []
    for session in sessions:
        row = rows.get(session["id"])
        if row is None or row.get("model_provider") != session["provider"]:
            mismatches.append(
                {
                    "id": session["id"],
                    "file_provider": session["provider"],
                    "db_provider": row.get("model_provider") if row else None,
                }
            )
    return {
        "codex_version": codex.version(),
        "schema_fingerprint": codex.schema_fingerprint(),
        "session_files": len(sessions),
        "database_threads": len(rows),
        "file_provider_counts": dict(sorted(file_providers.items())),
        "database_provider_counts": dict(sorted(db_providers.items())),
        "model_counts": dict(sorted(models.items())),
        "mismatches": mismatches,
        "normalization_candidates": sum(
            count for provider, count in file_providers.items() if provider != "custom"
        ),
    }


def create_normalize_plan(output: Path, target: str = "custom") -> Dict[str, Any]:
    rows = _thread_rows()
    items: List[Dict[str, Any]] = []
    seen_ids = set()
    for path in _session_paths():
        session = _read_session(path)
        if session["id"] in seen_ids:
            raise RelayError("发现重复会话 ID，拒绝计划: %s" % session["id"])
        seen_ids.add(session["id"])
        if session["provider"] == target:
            continue
        row = rows.get(session["id"])
        if row is None:
            raise RelayError("会话没有对应 threads 索引，拒绝计划: %s" % session["id"])
        if row.get("model_provider") != session["provider"]:
            raise RelayError("JSONL 与 threads Provider 不一致，拒绝计划: %s" % session["id"])
        session["target_provider"] = target
        session["model"] = row.get("model")
        items.append(session)
    plan: Dict[str, Any] = {
        "schema_version": 1,
        "kind": "normalize-provider",
        "created_at": utc_now(),
        "codex_version": codex.version(),
        "schema_fingerprint": codex.schema_fingerprint(),
        "state_db": str(state_db_path().resolve()),
        "target_provider": target,
        "items": items,
    }
    plan["confirmation_sha256"] = digest_json(plan)
    write_json(output, plan)
    return plan


def _validate_plan(plan: Dict[str, Any], confirm: str, kind: str) -> None:
    if plan.get("schema_version") != 1 or plan.get("kind") != kind:
        raise RelayError("计划文件类型或版本无效")
    expected = digest_json(plan)
    if plan.get("confirmation_sha256") != expected or confirm != expected:
        raise RelayError("确认摘要不匹配，拒绝执行")


def _assert_clients_closed() -> None:
    clients = codex.active_clients()
    if clients:
        raise RelayError("检测到 Codex/ChatGPT 正在运行，请先退出:\n" + "\n".join(clients))


class HistoryLock:
    def __init__(self) -> None:
        self.path = relay_home() / "history.lock"
        self.fd: Optional[int] = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            raise RelayError("已有历史写入操作进行中: %s" % self.path) from error
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self.fd is not None:
            os.close(self.fd)
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def _sqlite_backup(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(source)) as source_db, sqlite3.connect(str(target)) as target_db:
        source_db.backup(target_db)


def _backup_for_plan(plan: Dict[str, Any]) -> Path:
    backup = relay_home() / "backups" / (timestamp() + "-" + plan["confirmation_sha256"][:12])
    backup.mkdir(parents=True, exist_ok=False)
    _sqlite_backup(state_db_path(), backup / "state_5.sqlite")
    write_json(backup / "plan.json", plan)
    manifest = {
        "schema_version": 1,
        "kind": "history-backup",
        "created_at": utc_now(),
        "source_plan_sha256": plan["confirmation_sha256"],
        "state_db_sha256": sha256_file(backup / "state_5.sqlite"),
        "items": [
            {
                "id": item["id"],
                "path": item["path"],
                "first_line_b64": item["first_line_b64"],
                "tail_sha256": item["tail_sha256"],
                "had_separator": item["had_separator"],
            }
            for item in plan["items"]
        ],
    }
    manifest["confirmation_sha256"] = digest_json(manifest)
    write_json(backup / "manifest.json", manifest)
    return backup


def _replace_first_provider(item: Dict[str, Any], target: str) -> None:
    path = Path(item["path"])
    current = _read_session(path)
    for key in ("id", "file_sha256", "first_line_sha256", "tail_sha256", "record_count"):
        if current[key] != item[key]:
            raise RelayError("会话在计划后发生变化: %s (%s)" % (path, key))
    raw = path.read_bytes()
    first, separator, tail = raw.partition(b"\n")
    replaced, count = PROVIDER_PATTERN.subn(
        lambda match: match.group(1) + json.dumps(target).encode("utf-8"), first, count=1
    )
    if count != 1:
        raise RelayError("无法精确替换 model_provider: %s" % path)
    atomic_write_bytes(path, replaced + (b"\n" if separator else b"") + tail)


def _validate_current_item(item: Dict[str, Any]) -> None:
    current = _read_session(Path(item["path"]))
    for key in ("id", "file_sha256", "first_line_sha256", "tail_sha256", "record_count"):
        if current[key] != item[key]:
            raise RelayError("会话在计划后发生变化: %s (%s)" % (item["path"], key))


def _restore_backup(backup: Path) -> None:
    manifest = read_json(backup / "manifest.json")
    if sha256_file(backup / "state_5.sqlite") != manifest.get("state_db_sha256"):
        raise RelayError("备份 SQLite 校验失败，拒绝恢复")
    prepared = []
    for item in manifest["items"]:
        path = Path(item["path"])
        raw = path.read_bytes()
        _, separator, tail = raw.partition(b"\n")
        if sha256_bytes(tail) != item["tail_sha256"]:
            raise RelayError("回滚时会话正文校验失败: %s" % path)
        original = base64.b64decode(item["first_line_b64"])
        current_first = raw.partition(b"\n")[0]
        if current_first != original:
            original_matches = PROVIDER_PATTERN.findall(original)
            if len(original_matches) != 1:
                raise RelayError("备份首行 Provider 格式无效: %s" % path)
            original_provider = original_matches[0][1]
            candidate, count = PROVIDER_PATTERN.subn(
                lambda match: match.group(1) + b'"' + original_provider + b'"',
                current_first,
                count=1,
            )
            if count != 1 or candidate != original:
                raise RelayError("回滚时会话首行存在非 Provider 变化: %s" % path)
        prepared.append((path, original, tail, item["had_separator"]))
    shutil.copy2(str(backup / "state_5.sqlite"), str(state_db_path()))
    for path, original, tail, had_separator in prepared:
        atomic_write_bytes(
            path, original + (b"\n" if had_separator else b"") + tail
        )


def apply_normalize(plan_path: Path, confirm: str) -> Dict[str, Any]:
    plan = read_json(plan_path)
    _validate_plan(plan, confirm, "normalize-provider")
    _assert_clients_closed()
    if codex.schema_fingerprint() != plan.get("schema_fingerprint"):
        raise RelayError("Codex threads schema 自生成计划后已变化")
    if codex.version() != plan.get("codex_version"):
        raise RelayError("Codex CLI 版本自生成计划后已变化")
    with HistoryLock():
        for item in plan["items"]:
            _validate_current_item(item)
        backup = _backup_for_plan(plan)
        try:
            for item in plan["items"]:
                _replace_first_provider(item, plan["target_provider"])
            with sqlite3.connect(str(state_db_path())) as connection:
                connection.execute("BEGIN IMMEDIATE")
                for item in plan["items"]:
                    cursor = connection.execute(
                        "UPDATE threads SET model_provider=? WHERE id=? AND model_provider=?",
                        (plan["target_provider"], item["id"], item["provider"]),
                    )
                    if cursor.rowcount != 1:
                        raise RelayError("threads 条件更新失败: %s" % item["id"])
                connection.commit()
            for item in plan["items"]:
                current = _read_session(Path(item["path"]))
                if (
                    current["provider"] != plan["target_provider"]
                    or current["tail_sha256"] != item["tail_sha256"]
                    or current["record_count"] != item["record_count"]
                ):
                    raise RelayError("迁移后会话校验失败: %s" % item["id"])
            rows = _thread_rows()
            for item in plan["items"]:
                if rows[item["id"]]["model_provider"] != plan["target_provider"]:
                    raise RelayError("迁移后数据库校验失败: %s" % item["id"])
        except Exception:
            _restore_backup(backup)
            raise
    return {"updated": len(plan["items"]), "backup": str(backup)}


def rollback(backup: Path, confirm: str) -> Dict[str, Any]:
    manifest = read_json(backup / "manifest.json")
    _validate_plan(manifest, confirm, "history-backup")
    _assert_clients_closed()
    with HistoryLock():
        _restore_backup(backup)
    return {"restored": len(manifest["items"]), "backup": str(backup)}


def create_tag_plan(output: Path, remove: bool = False) -> Dict[str, Any]:
    rows = _thread_rows()
    items: List[Dict[str, Any]] = []
    for row in rows.values():
        title = row.get("title") or ""
        stripped = title
        for prefix in TAG_PREFIXES:
            if stripped.startswith(prefix):
                stripped = stripped[len(prefix) :]
        if remove:
            new_title = stripped
        elif (row.get("model") or "").lower().startswith("gpt"):
            new_title = "[GPT] " + stripped
        elif (row.get("model") or "").lower().startswith("deepseek"):
            new_title = "[DS] " + stripped
        else:
            continue
        if new_title != title:
            items.append({"id": row["id"], "old_title": title, "new_title": new_title})
    plan: Dict[str, Any] = {
        "schema_version": 1,
        "kind": "tag-titles",
        "created_at": utc_now(),
        "schema_fingerprint": codex.schema_fingerprint(),
        "remove": remove,
        "items": items,
    }
    plan["confirmation_sha256"] = digest_json(plan)
    write_json(output, plan)
    return plan


def apply_tag_plan(plan_path: Path, confirm: str) -> Dict[str, Any]:
    plan = read_json(plan_path)
    _validate_plan(plan, confirm, "tag-titles")
    _assert_clients_closed()
    if codex.schema_fingerprint() != plan.get("schema_fingerprint"):
        raise RelayError("Codex threads schema 自生成计划后已变化")
    with HistoryLock():
        backup = relay_home() / "backups" / (timestamp() + "-titles")
        backup.mkdir(parents=True, exist_ok=False)
        _sqlite_backup(state_db_path(), backup / "state_5.sqlite")
        write_json(backup / "tag-plan.json", plan)
        try:
            with sqlite3.connect(str(state_db_path())) as connection:
                connection.execute("BEGIN IMMEDIATE")
                for item in plan["items"]:
                    cursor = connection.execute(
                        "UPDATE threads SET title=? WHERE id=? AND title=?",
                        (item["new_title"], item["id"], item["old_title"]),
                    )
                    if cursor.rowcount != 1:
                        raise RelayError("标题在计划后发生变化: %s" % item["id"])
                connection.commit()
        except Exception:
            shutil.copy2(str(backup / "state_5.sqlite"), str(state_db_path()))
            raise
    return {"updated": len(plan["items"]), "backup": str(backup)}
