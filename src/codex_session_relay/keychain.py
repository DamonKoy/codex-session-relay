from __future__ import annotations

import getpass
import os
import pty
import select
import subprocess
import sys
import termios
import time
from typing import Optional, Tuple

from .errors import RelayError


SECURITY_COMMAND = "/usr/bin/security"


def _require_macos() -> None:
    if sys.platform != "darwin":
        raise RelayError("当前版本的安全凭证存储仅支持 macOS Keychain")


def _security_find(service_name: str, account: str) -> Tuple[int, str, str]:
    """Read one generic password without ever putting its value in argv."""
    result = subprocess.run(
        [
            SECURITY_COMMAND,
            "find-generic-password",
            "-a",
            account,
            "-s",
            service_name,
            "-w",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout.rstrip("\n"), result.stderr.strip()


def _store_command(service_name: str, account: str) -> list[str]:
    return [
        SECURITY_COMMAND,
        "add-generic-password",
        "-a",
        account,
        "-s",
        service_name,
        "-U",
        "-w",
    ]


def _security_store(service_name: str, account: str, secret: str) -> int:
    """Answer Keychain's no-echo prompt through a PTY, never an argv value."""
    command = _store_command(service_name, account)
    child_pid, master = pty.fork()
    if child_pid == 0:  # pragma: no cover - replaced by exec in the child
        try:
            os.execv(SECURITY_COMMAND, command)
        finally:
            os._exit(127)
    active_pid = child_pid
    try:
        attributes = termios.tcgetattr(master)
        attributes[3] &= ~termios.ECHO
        termios.tcsetattr(master, termios.TCSANOW, attributes)
        # New items ask for entry plus confirmation. Wait for each prompt:
        # `security` may flush queued terminal input before the second prompt.
        secret_line = (secret + "\n").encode("utf-8")
        answers_sent = 0
        prompt_buffer = b""
        deadline = time.monotonic() + 30
        while True:
            waited_pid, wait_status = os.waitpid(child_pid, os.WNOHANG)
            if waited_pid:
                active_pid = 0
                return os.waitstatus_to_exitcode(wait_status)
            if time.monotonic() >= deadline:
                raise RelayError("写入 macOS Keychain 超时；请确认登录钥匙串已解锁")
            readable, _, _ = select.select([master], [], [], 0.1)
            if readable:
                try:
                    prompt = os.read(master, 4096)
                except OSError:
                    prompt = b""
                prompt_buffer += prompt
                if (
                    answers_sent < 2
                    and (b": " in prompt_buffer or prompt_buffer.rstrip().endswith(b":"))
                ):
                    os.write(master, secret_line)
                    answers_sent += 1
                    prompt_buffer = b""
    finally:
        os.close(master)
        if active_pid:
            os.kill(active_pid, 9)
            os.waitpid(active_pid, 0)


def read_secret(service_name: str, account: Optional[str] = None) -> Optional[str]:
    _require_macos()
    status, secret, error = _security_find(
        service_name, account or getpass.getuser()
    )
    if status == 0:
        return secret
    # macOS 15 may report an intermediate errSecParam message while the
    # command still ends with the documented "item not found" exit status.
    if status == 44:
        return None
    detail = error.splitlines()[-1] if error else "未知错误"
    raise RelayError("读取 macOS Keychain 失败（security=%s）：%s" % (status, detail))


def write_secret(service_name: str, secret: str, account: Optional[str] = None) -> None:
    _require_macos()
    if not secret:
        raise RelayError("API Key 不能为空")
    account_name = account or getpass.getuser()
    status = _security_store(service_name, account_name, secret)
    if status != 0:
        raise RelayError("写入 macOS Keychain 失败（security=%s）" % status)
    stored = read_secret(service_name, account_name)
    if stored != secret:
        raise RelayError("Keychain 写入后读取校验失败")


def delete_secret(service_name: str, account: Optional[str] = None) -> bool:
    """Delete one exact Relay-owned Keychain item; primarily used by validation."""
    _require_macos()
    account_name = account or getpass.getuser()
    status, _, error = _security_find(service_name, account_name)
    if status == 44:
        return False
    if status != 0:
        detail = error.splitlines()[-1] if error else "未知错误"
        raise RelayError("查找待删除 Keychain 项失败：%s" % detail)
    result = subprocess.run(
        [
            SECURITY_COMMAND,
            "delete-generic-password",
            "-a",
            account_name,
            "-s",
            service_name,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = result.stderr.strip().splitlines()[-1] if result.stderr else "未知错误"
        raise RelayError("删除 Keychain 项失败：%s" % detail)
    return True
