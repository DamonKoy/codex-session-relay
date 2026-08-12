from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .errors import RelayError
from .util import utc_now


ROLE_LABELS = {
    "creator": ("Primary maintainer", "主要维护者（创建者）"),
    "primary-maintainer": ("Primary maintainer", "主要维护者"),
    "core-maintainer": ("Core maintainer", "核心维护者"),
}


def _github_json(url: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "codex-session-relay/0.1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise RelayError("GitHub 仓库不存在或尚未公开，拒绝生成最终申请材料") from error
        raise RelayError("GitHub API 请求失败，HTTP %s" % error.code) from error
    except urllib.error.URLError as error:
        raise RelayError("无法访问 GitHub API: %s" % error.reason) from error


def fetch_metrics(repo: str) -> Dict[str, Any]:
    if repo.count("/") != 1:
        raise RelayError("--repo 必须使用 owner/name 格式")
    escaped = "/".join(urllib.parse.quote(part, safe="") for part in repo.split("/"))
    data = _github_json("https://api.github.com/repos/%s" % escaped)
    contributors: List[Any] = []
    for page in range(1, 101):
        batch = _github_json(
            "https://api.github.com/repos/%s/contributors?per_page=100&anon=true&page=%s"
            % (escaped, page)
        )
        if not isinstance(batch, list):
            break
        contributors.extend(batch)
        if len(batch) < 100:
            break
    return {
        "repo": repo,
        "url": data["html_url"],
        "description": data.get("description") or "",
        "stars": int(data.get("stargazers_count") or 0),
        "forks": int(data.get("forks_count") or 0),
        "contributors": len(contributors),
        "license": ((data.get("license") or {}).get("spdx_id") or "No detected license"),
        "default_branch": data.get("default_branch") or "unknown",
        "language": data.get("language") or "Not detected",
        "open_issues": int(data.get("open_issues_count") or 0),
        "fetched_at": utc_now(),
    }


def _field(title: str, english: str, chinese: str, reason: str) -> str:
    length = len(english)
    if length > 500:
        raise RelayError("申请字段超过 500 个英文字符: %s (%s)" % (title, length))
    return (
        "### %s\n\n"
        "**Recommended English (%s/500 characters)**\n\n%s\n\n"
        "**中文翻译**\n\n%s\n\n"
        "**Why**: %s\n" % (title, length, english, chinese, reason)
    )


def _metric_count(value: int, singular: str, plural: str = "") -> str:
    return "%s %s" % (value, singular if value == 1 else (plural or singular + "s"))


def render(repo: str, role: str, output: Path) -> Dict[str, Any]:
    if role not in ROLE_LABELS:
        raise RelayError("未知角色: %s" % role)
    metrics = fetch_metrics(repo)
    role_en, role_zh = ROLE_LABELS[role]
    proof = "%s, %s, and %s" % (
        _metric_count(metrics["stars"], "star"),
        _metric_count(metrics["forks"], "fork"),
        _metric_count(metrics["contributors"], "public contributor"),
    )
    answers = [
        (
            "1. Why the repository qualifies",
            "Codex Session Relay is an Apache-2.0 macOS CLI that keeps Codex official authentication separate from external provider keys and creates reviewed, redacted cross-model handoffs. It includes reversible JSONL/SQLite migration, Keychain integration, read-only defaults, tests, and security documentation. GitHub currently reports %s. It gives agent-tool users a local-first reference for provider isolation and explicit review at trust boundaries."
            % proof,
            "Codex Session Relay 是 Apache-2.0 的 macOS CLI，将 Codex 官方认证与外部 Provider 密钥隔离，并创建经审阅、脱敏的跨模型接力任务。项目包含可回滚的 JSONL/SQLite 迁移、Keychain 集成、默认只读、安全文档和测试。GitHub 当前公开指标为 %s Star、%s Fork、%s 位贡献者，为 Agent 工具用户提供本地优先的 Provider 隔离及信任边界人工复核参考实现。"
            % (metrics["stars"], metrics["forks"], metrics["contributors"]),
            "It uses live GitHub metrics and verifiable repository artifacts.",
        ),
        (
            "2. How API credits will be used",
            "Credits will support maintainer-reviewed automation for redacted issue triage, PR risk summaries, compatibility-test generation for Codex/provider changes, regression clustering, and draft release notes. Inputs will exclude credentials and private transcripts. Outputs will be advisory: no automatic merge, release, network action, or execution of untrusted contributor code. Usage and acceptance will be logged for maintainability and abuse review."
            ,
            "额度将用于经维护者复核的自动化：脱敏 Issue 分类、PR 风险摘要、Codex/Provider 兼容性测试生成、回归聚类和 Release Notes 草稿。输入不含凭证或私密对话；输出只作建议，不自动合并、发布、联网或执行不可信贡献代码，并记录使用及采纳情况。",
            "It names bounded maintenance jobs and explicit human-control gates.",
        ),
        (
            "3. Additional information",
            "This is an unofficial Alpha project, not affiliated with OpenAI or DeepSeek. Its attack surface includes untrusted provider URLs and handoff text, prompt injection, child-process credentials, shell/network/file access, SQLite/JSONL migration, and third-party CI or code contributions. Codex Security would help review changes across those paths. It does not share subscription quota, decrypt reasoning, or promise same-thread continuation; external providers are billed separately."
            ,
            "这是与 OpenAI、DeepSeek 均无隶属关系的非官方 Alpha 项目。真实攻击面包括不可信 Provider URL 和接力文本、Prompt Injection、子进程凭证、Shell/网络/文件访问、SQLite/JSONL 迁移以及第三方 CI 或代码贡献；Codex Security 可帮助评审这些路径上的改动。项目不共享订阅额度、不解密推理内容，也不承诺原线程续聊，外部 Provider 独立计费。",
            "It states concrete security paths and preserves accurate product boundaries.",
        ),
    ]
    sections = [
        "# Codex for Open Source application",
        "",
        "> Generated from public GitHub data at `%s`. Re-check metrics immediately before submission."
        % metrics["fetched_at"],
        "",
        "## Verified repository analysis",
        "",
        "1. **Purpose**: Safely run Codex with official authentication and separately authenticated Responses-compatible providers, then create reviewed cross-provider handoffs.",
        "2. **Public metrics**: %s." % proof.capitalize(),
        "3. **Components**: provider/key management, runtime launcher, session audit/migration/rollback, title tagging, safe handoff packages, application renderer, tests, and release tooling.",
        "4. **Users**: Codex users and open-source maintainers who need multiple providers without merging credentials or trusting raw transcripts.",
        "5. **Ecosystem value**: A local-first, reversible reference workflow for provider isolation and explicit human review at agent trust boundaries.",
        "6. **Agent/tooling scope**: AI agents, CLI configuration, Keychain, SQLite/JSONL migration, subprocess execution, network providers, and third-party contributions.",
        "7. **Security risks**: malicious code/configuration, prompt injection, credential leaks, unauthorized requests, filesystem/session corruption, dependency or release compromise, and risky contributions.",
        "8. **Codex Security fit**: Review data-flow and execution paths that cross transcript, credential, provider, shell, network, and filesystem boundaries.",
        "9. **API credit use**: redacted issue triage, PR risk review, compatibility tests, regression analysis, and draft release notes with maintainer approval.",
        "",
        "## Fixed form values",
        "",
        "- **GitHub username**: `%s`" % metrics["repo"].split("/", 1)[0],
        "- **GitHub repository URL**: %s" % metrics["url"],
        "- **Role**: %s (%s)" % (role_en, role_zh),
        "- **Interests**: Codex Security; API credits for my project",
        "- **Fill manually**: first name, last name, ChatGPT account email, and OpenAI Organization ID",
        "",
        "## Application fields",
        "",
    ]
    for answer in answers:
        sections.append(_field(*answer))
    sections.extend(["## Most recommended submission version", ""])
    for index, (_, english, _, _) in enumerate(answers, 1):
        sections.extend(["### %s" % index, "", english, ""])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(sections).rstrip() + "\n", encoding="utf-8")
    return {"output": str(output.resolve()), "metrics": metrics, "fields": 3}
