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
    "creator": ("Creator", "创建者"),
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


def render(repo: str, role: str, output: Path) -> Dict[str, Any]:
    if role not in ROLE_LABELS:
        raise RelayError("未知角色: %s" % role)
    metrics = fetch_metrics(repo)
    role_en, role_zh = ROLE_LABELS[role]
    proof = "%s stars, %s forks, and %s public contributors" % (
        metrics["stars"],
        metrics["forks"],
        metrics["contributors"],
    )
    answers = [
        (
            "1. Role",
            "I am the %s of Codex Session Relay. I designed its provider isolation, safe handoff workflow, session migration safeguards, tests, release process, and security policy, and I am responsible for reviewing contributions and maintaining compatibility with Codex and external Responses-compatible providers."
            % role_en.lower(),
            "我是 Codex Session Relay 的%s。我负责 Provider 隔离、安全接力、会话迁移保护、测试、发布流程和安全策略，并长期评审贡献及维护 Codex 与外部兼容 Provider 的适配。"
            % role_zh,
            "It states concrete ownership and long-term maintenance duties.",
        ),
        (
            "2. Why the repository qualifies",
            "Codex Session Relay is an Apache-2.0 macOS CLI for using Codex official authentication alongside separately billed external providers, keeping local tasks visible and transferring only reviewed, redacted conversation text. The repository currently has %s. It provides source, tests, security documentation, rollback tooling, and a contribution workflow for agent-tool users and maintainers."
            % proof,
            "Codex Session Relay 是 Apache-2.0 的 macOS CLI，可并用 Codex 官方认证与独立计费的外部 Provider，统一本地任务可见性，并只传递经审阅和脱敏的对话文本。仓库当前公开指标为%s Star、%s Fork、%s 位贡献者，并提供源码、测试、安全文档、回滚工具和贡献流程。"
            % (metrics["stars"], metrics["forks"], metrics["contributors"]),
            "It uses live GitHub metrics and verifiable repository artifacts.",
        ),
        (
            "3. Why the project needs Codex Security",
            "The CLI reads agent transcripts, injects provider credentials into child-process environments, writes Codex session metadata and SQLite indexes, and launches agents with shell, network, and file access. Malicious provider URLs, prompt injection in handoff text, secret-exfiltration changes, unsafe migration code, or a compromised contribution could leak keys, corrupt sessions, or execute attacker-controlled commands. Codex Security can review these concrete paths."
            ,
            "该 CLI 会读取 Agent 对话、向子进程注入 Provider 凭证、写入 Codex 会话元数据和 SQLite 索引，并启动具备 Shell、网络和文件访问能力的 Agent。恶意 Provider URL、接力文本中的 Prompt Injection、窃密改动、不安全迁移代码或被攻陷的贡献都可能泄露密钥、破坏会话或执行攻击者命令。",
            "It identifies the exact data and execution boundaries attackers could abuse.",
        ),
        (
            "4. How API credits will be used",
            "Credits will support maintainer-reviewed automation for redacted issue triage, PR risk summaries, compatibility-test generation for Codex/provider changes, regression clustering, and draft release notes. Inputs will exclude credentials and private transcripts. Outputs will be advisory: no automatic merge, release, network action, or execution of untrusted contributor code. Usage and acceptance will be logged for maintainability and abuse review."
            ,
            "额度将用于经维护者复核的自动化：脱敏 Issue 分类、PR 风险摘要、Codex/Provider 兼容性测试生成、回归聚类和 Release Notes 草稿。输入不含凭证或私密对话；输出只作建议，不自动合并、发布、联网或执行不可信贡献代码，并记录使用及采纳情况。",
            "It names bounded maintenance jobs and explicit human-control gates.",
        ),
        (
            "5. Additional information",
            "This is an unofficial project and is not affiliated with OpenAI or DeepSeek. Codex subscription authentication and external-provider API billing remain separate. Cross-provider handoff creates a new task from user-reviewed readable text; it does not transfer subscription quota, decrypt reasoning, or promise same-thread continuation. v0.1.0 is macOS-first, uses Keychain, defaults handoffs to read-only, and requires SHA-256 confirmation before writes or sends."
            ,
            "这是非官方项目，与 OpenAI 或 DeepSeek 无隶属关系。Codex 订阅认证与外部 Provider API 计费相互独立。跨 Provider 接力会从用户审阅的可读文本创建新任务，不转移订阅额度、不解密推理内容，也不承诺原线程续聊。v0.1.0 优先支持 macOS，使用 Keychain，接力默认只读，写入或发送前要求 SHA-256 确认。",
            "It prevents misleading claims and states the project's safety defaults.",
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
    return {"output": str(output.resolve()), "metrics": metrics, "fields": 5}
