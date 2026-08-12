from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

from .errors import RelayError
from .paths import config_path
from .util import read_json, write_json


SCHEMA_VERSION = 1
BUILTIN_PROVIDERS: Dict[str, Dict[str, Any]] = {
    "openai": {
        "display_name": "OpenAI Official",
        "auth_mode": "codex_official",
        "model": None,
        "base_url": None,
        "wire_api": "responses",
        "keychain_service": None,
        "env_key": None,
    },
    "deepseek": {
        "display_name": "DeepSeek",
        "auth_mode": "api_key",
        "model": "deepseek-v4-flash",
        "base_url": None,
        "wire_api": "responses",
        "keychain_service": "codex-session-relay.provider.deepseek",
        "env_key": "OPENAI_API_KEY",
        "setup_required": "responses_gateway",
    },
}


def default_config() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "history_provider": "custom",
        "providers": copy.deepcopy(BUILTIN_PROVIDERS),
    }


def validate_base_url(value: str, allow_insecure_localhost: bool = False) -> str:
    parsed = urlparse(value)
    if parsed.hostname == "api.deepseek.com":
        raise RelayError(
            "DeepSeek 官方地址当前不提供 Codex 所需的 Responses API；"
            "请填写一个明确支持 /responses 的网关地址"
        )
    if parsed.scheme == "https" and parsed.hostname:
        return value.rstrip("/") + "/"
    localhost = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme == "http" and localhost and allow_insecure_localhost:
        return value.rstrip("/") + "/"
    raise RelayError(
        "Provider base URL 必须使用 HTTPS；仅 localhost 可配合 "
        "--allow-insecure-localhost 显式放行 HTTP"
    )


def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    if config.get("schema_version") != SCHEMA_VERSION:
        raise RelayError("不支持的配置 schema_version")
    if config.get("history_provider") != "custom":
        raise RelayError("当前版本只支持统一历史桶 custom")
    providers = config.get("providers")
    if not isinstance(providers, dict) or not providers:
        raise RelayError("配置中缺少 providers")
    for name, provider in providers.items():
        if not isinstance(name, str) or not name or not isinstance(provider, dict):
            raise RelayError("Provider 配置格式无效")
        if provider.get("wire_api") != "responses":
            raise RelayError("当前版本只支持 Responses-compatible Provider")
        if provider.get("auth_mode") not in {"codex_official", "api_key"}:
            raise RelayError("Provider auth_mode 无效: %s" % name)
        if provider.get("auth_mode") == "api_key":
            base_url = provider.get("base_url")
            pending_gateway = (
                base_url is None
                and provider.get("setup_required") == "responses_gateway"
            )
            if not isinstance(base_url, str) and not pending_gateway:
                raise RelayError("外部 Provider 缺少 base_url: %s" % name)
            if isinstance(base_url, str):
                parsed = urlparse(base_url)
                local_http = parsed.scheme == "http" and parsed.hostname in {
                    "localhost",
                    "127.0.0.1",
                    "::1",
                }
                if parsed.scheme != "https" and not local_http:
                    raise RelayError("外部 Provider base_url 不安全: %s" % name)
            for key in ("model", "keychain_service", "env_key"):
                if not provider.get(key):
                    raise RelayError("外部 Provider 缺少 %s: %s" % (key, name))
    return config


def load_config(create: bool = True) -> Dict[str, Any]:
    path = config_path()
    if not path.exists():
        config = default_config()
        if create:
            save_config(config)
        return config
    config = read_json(path)
    deepseek = (config.get("providers") or {}).get("deepseek") or {}
    if (
        deepseek.get("wire_api") == "responses"
        and deepseek.get("base_url") in {
            "https://api.deepseek.com",
            "https://api.deepseek.com/",
        }
    ):
        # Early v0.1.0 drafts incorrectly assumed that DeepSeek's official
        # OpenAI-compatible API included /responses. Preserve the profile and
        # Keychain reference, but require a real Responses gateway explicitly.
        config = copy.deepcopy(config)
        config["providers"]["deepseek"]["base_url"] = None
        config["providers"]["deepseek"]["setup_required"] = "responses_gateway"
        save_config(config)
    config = validate_config(config)
    if path.stat().st_mode & 0o077:
        raise RelayError("配置权限过宽，应为 0600: %s" % path)
    return config


def save_config(config: Dict[str, Any]) -> None:
    validate_config(config)
    path = config_path()
    write_json(path, config, mode=0o600)
    os.chmod(str(path), 0o600)


def provider_names(config: Dict[str, Any]) -> List[str]:
    return sorted(config["providers"])


def get_provider(config: Dict[str, Any], name: str) -> Dict[str, Any]:
    try:
        return config["providers"][name]
    except KeyError as error:
        raise RelayError("未知 Provider: %s" % name) from error


def add_provider(
    config: Dict[str, Any],
    name: str,
    display_name: str,
    model: str,
    base_url: str,
    env_key: str,
    allow_insecure_localhost: bool,
) -> Dict[str, Any]:
    if not name.replace("-", "").replace("_", "").isalnum():
        raise RelayError("Provider 名称只能包含字母、数字、连字符和下划线")
    if name in config["providers"]:
        raise RelayError("Provider 已存在: %s" % name)
    updated = copy.deepcopy(config)
    updated["providers"][name] = {
        "display_name": display_name,
        "auth_mode": "api_key",
        "model": model,
        "base_url": validate_base_url(base_url, allow_insecure_localhost),
        "wire_api": "responses",
        "keychain_service": "codex-session-relay.provider.%s" % name,
        "env_key": env_key,
    }
    save_config(updated)
    return updated


def configure_provider(
    config: Dict[str, Any],
    name: str,
    base_url: str,
    model: str,
    env_key: str,
    allow_insecure_localhost: bool,
) -> Dict[str, Any]:
    provider = get_provider(config, name)
    if provider["auth_mode"] != "api_key":
        raise RelayError("官方认证 Provider 不允许配置外部 API 地址")
    updated = copy.deepcopy(config)
    target = updated["providers"][name]
    target["base_url"] = validate_base_url(base_url, allow_insecure_localhost)
    target["model"] = model or target["model"]
    target["env_key"] = env_key or target["env_key"]
    target.pop("setup_required", None)
    save_config(updated)
    return updated
