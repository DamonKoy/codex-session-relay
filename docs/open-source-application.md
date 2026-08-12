# Codex for Open Source application — pre-publication draft

> **Not ready to submit.** The local repository has not been published, so no GitHub URL, Stars, Forks, or Contributors can yet be verified. Do not replace these with account-level or unrelated-repository metrics. After publication, run `codex-relay application render --repo DamonKoy/codex-session-relay --role creator`; the renderer refuses a 404 and produces a timestamped, metrics-backed final version.

## Repository analysis

1. **Main purpose and problem**: Codex Session Relay safely combines Codex official authentication with separately authenticated Responses-compatible providers. It solves split local history and unsafe ad-hoc transcript copying without merging credentials, quotas, or billing.
2. **Public metrics**: Not yet available because this is a local-only pre-publication repository. The final renderer fetches repository Stars, Forks, Contributors, license, language, default branch, and open issue count from GitHub's public API.
3. **Functions and components**: Provider/config management, macOS Keychain, Codex runtime launcher, history audit, confirmed migration and rollback, title tagging, reviewed handoff packages, application rendering, deterministic builds, tests, and security/release documentation.
4. **Users**: Codex users, AI-agent developers, and open-source maintainers who need multiple model providers while preserving explicit credential, transcript, filesystem, shell, and billing boundaries.
5. **Ecosystem value**: A local-first, reversible reference implementation for provider isolation and human-reviewed cross-model handoffs, with no runtime dependency and synthetic test fixtures.
6. **Relevant scenarios**: AI agents, CLI tooling, model-provider configuration, Keychain, JSONL/SQLite migration, subprocess/code execution, network APIs, automation, plugins/adapters on the roadmap, and third-party contributions.
7. **Security risks**: malicious Provider endpoints, malicious code or scripts, prompt injection in historical text, credential leakage, unauthorized network calls, filesystem/session corruption, release/supply-chain compromise, and unsafe third-party contributions.
8. **How Codex Security helps**: Review the exact paths where untrusted transcript/config/contributor data crosses credential, child-process, network, database, shell, and filesystem boundaries; detect changes that weaken confirmation, redaction, rollback, or sandbox controls.
9. **How API credits help**: Maintainer-reviewed automation for redacted issue triage, PR risk summaries, compatibility-test generation, regression clustering, and draft Release Notes. It will not auto-merge, auto-release, execute untrusted contributor code, or send private transcripts.

## Application fields

### 1. Explain your role

**Recommended English (308/500 characters)**

I am the creator of Codex Session Relay. I designed its provider isolation, safe handoff workflow, session migration safeguards, tests, release process, and security policy, and I am responsible for reviewing contributions and maintaining compatibility with Codex and external Responses-compatible providers.

**中文翻译**

我是 Codex Session Relay 的创建者。我设计了 Provider 隔离、安全接力、会话迁移保护、测试、发布流程和安全策略，并负责评审贡献以及长期维护 Codex 与外部 Responses-compatible Provider 的兼容性。

**Why**: It states concrete ownership and long-term maintenance duties.

### 2. Why does this repository qualify?

**Recommended English (428/500 characters)**

Codex Session Relay is an Apache-2.0 macOS CLI for using Codex official authentication alongside separately billed external providers, keeping local tasks visible and transferring only reviewed, redacted conversation text. It includes source, tests, security documentation, rollback tooling, and a contribution workflow. Public metrics are intentionally omitted from this pre-publication draft and must be fetched after release.

**中文翻译**

Codex Session Relay 是 Apache-2.0 的 macOS CLI，可并用 Codex 官方认证与独立计费的外部 Provider，统一本地任务可见性，并只传递经审阅和脱敏的对话文本。项目包含源码、测试、安全文档、回滚工具和贡献流程。本预发布草稿有意不写公开指标，发布后必须重新获取。

**Why**: It describes verifiable artifacts and explicitly prevents invented pre-release metrics.

### 3. Why does your project need Codex Security?

**Recommended English (467/500 characters)**

The CLI reads agent transcripts, injects provider credentials into child-process environments, writes Codex session metadata and SQLite indexes, and launches agents with shell, network, and file access. Malicious provider URLs, prompt injection in handoff text, secret-exfiltration changes, unsafe migration code, or a compromised contribution could leak keys, corrupt sessions, or execute attacker-controlled commands. Codex Security can review these concrete paths.

**中文翻译**

该 CLI 会读取 Agent 对话、向子进程环境注入 Provider 凭证、写入 Codex 会话元数据和 SQLite 索引，并启动具备 Shell、网络和文件访问能力的 Agent。恶意 Provider URL、接力文本中的 Prompt Injection、窃密改动、不安全迁移代码或被攻陷的贡献都可能泄露密钥、破坏会话或执行攻击者命令；Codex Security 可评审这些真实路径。

**Why**: It identifies the exact data and execution boundaries attackers could abuse.

### 4. How will you use API credits for your project?

**Recommended English (449/500 characters)**

Credits will support maintainer-reviewed automation for redacted issue triage, PR risk summaries, compatibility-test generation for Codex/provider changes, regression clustering, and draft release notes. Inputs will exclude credentials and private transcripts. Outputs will be advisory: no automatic merge, release, network action, or execution of untrusted contributor code. Usage and acceptance will be logged for maintainability and abuse review.

**中文翻译**

额度将用于经维护者复核的自动化：脱敏 Issue 分类、PR 风险摘要、Codex/Provider 兼容性测试生成、回归聚类和 Release Notes 草稿。输入不含凭证或私密对话；输出只作建议，不自动合并、发布、联网或执行不可信贡献代码，并记录使用及采纳情况。

**Why**: It names bounded maintenance jobs and explicit human-control gates.

### 5. Anything else to add?

**Recommended English (462/500 characters)**

This is an unofficial project and is not affiliated with OpenAI or DeepSeek. Codex subscription authentication and external-provider API billing remain separate. Cross-provider handoff creates a new task from user-reviewed readable text; it does not transfer subscription quota, decrypt reasoning, or promise same-thread continuation. v0.1.0 is macOS-first, uses Keychain, defaults handoffs to read-only, and requires SHA-256 confirmation before writes or sends.

**中文翻译**

这是非官方项目，与 OpenAI 或 DeepSeek 无隶属关系。Codex 订阅认证与外部 Provider API 计费相互独立。跨 Provider 接力从用户审阅的可读文本创建新任务，不转移订阅额度、不解密推理内容，也不承诺原线程续聊。v0.1.0 优先支持 macOS，使用 Keychain，接力默认只读，写入或发送前要求 SHA-256 确认。

**Why**: It prevents misleading claims and states the project's safety defaults.

## Most recommended submission version

This section is intentionally withheld from the pre-publication draft. The final renderer will include all five English answers with live public metrics and no placeholders only after the repository URL resolves.

