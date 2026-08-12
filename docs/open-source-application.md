# Codex for Open Source application — pre-publication draft

> **Not ready to submit.** The repository is not public yet, so GitHub metrics cannot be verified. After publication, run `codex-relay application render --repo DamonKoy/codex-session-relay --role creator`. The renderer rejects a public 404, fetches current GitHub data, maps Creator to Primary maintainer, and produces the current three text fields.

## Repository analysis

1. **Main purpose and problem**: Codex Session Relay safely combines Codex official authentication with separately authenticated Responses-compatible providers. It addresses split local history and unsafe transcript copying without merging credentials, quotas, or billing.
2. **Public metrics**: Not yet available for this local-only repository. The final renderer fetches Stars, Forks, Contributors, license, language, default branch, and open issue count from GitHub's public API.
3. **Functions and components**: Provider/config management, macOS Keychain, runtime launcher, history audit, confirmed migration and rollback, title tagging, reviewed handoff packages, application rendering, deterministic builds, tests, and security/release documentation.
4. **Users**: Codex users, AI-agent developers, and open-source maintainers who need multiple model providers while preserving credential, transcript, filesystem, shell, network, and billing boundaries.
5. **Ecosystem value**: A local-first, reversible reference implementation for provider isolation and human-reviewed cross-model handoffs, with no runtime dependency and synthetic test fixtures.
6. **Relevant scenarios**: AI agents, CLI tooling, model-provider configuration, Keychain, JSONL/SQLite migration, subprocess execution, network APIs, automation, future adapters/plugins, and third-party contributions.
7. **Security risks**: Malicious Provider endpoints or code, prompt injection in historical text, credential leakage, unauthorized requests, filesystem/session corruption, release or supply-chain compromise, and unsafe contributions.
8. **How Codex Security helps**: Review paths where untrusted transcript, configuration, and contributor data cross credential, child-process, network, database, shell, and filesystem boundaries, including changes that weaken confirmation, redaction, rollback, or sandbox controls.
9. **How API credits help**: Maintainer-reviewed automation for redacted issue triage, PR risk summaries, compatibility-test generation, regression clustering, and draft Release Notes. It will not auto-merge, auto-release, execute untrusted contributor code, or send private transcripts.

## Current form mapping

- **GitHub username**: `DamonKoy`
- **GitHub repository URL**: generated from the live public repository
- **Role**: Primary maintainer (Creator maps to this current form option)
- **Interests**: Codex Security; API credits for my project
- **Fill manually and never store in generated files**: first name, last name, ChatGPT account email, and OpenAI Organization ID

## Application fields

### 1. Why does this repository qualify?

**Recommended English (428/500 characters)**

Codex Session Relay is an Apache-2.0 macOS CLI that keeps Codex official authentication separate from external provider keys and creates reviewed, redacted cross-model handoffs. It includes reversible JSONL/SQLite migration, Keychain integration, read-only defaults, tests, security documentation, and a contribution workflow. Public metrics are omitted until the repository is live; the final renderer fetches them from GitHub.

**中文翻译**

Codex Session Relay 是 Apache-2.0 的 macOS CLI，将 Codex 官方认证与外部 Provider 密钥隔离，并创建经审阅、脱敏的跨模型接力。项目提供可回滚的 JSONL/SQLite 迁移、Keychain 集成、默认只读、安全文档、测试和贡献流程。公开前不填写指标，最终生成器将在仓库上线后从 GitHub 获取真实数据。

**Why**: It describes verifiable artifacts and explicitly prevents invented pre-release metrics.

### 2. How will you use API credits for your project?

**Recommended English (449/500 characters)**

Credits will support maintainer-reviewed automation for redacted issue triage, PR risk summaries, compatibility-test generation for Codex/provider changes, regression clustering, and draft release notes. Inputs will exclude credentials and private transcripts. Outputs will be advisory: no automatic merge, release, network action, or execution of untrusted contributor code. Usage and acceptance will be logged for maintainability and abuse review.

**中文翻译**

额度将用于经维护者复核的自动化：脱敏 Issue 分类、PR 风险摘要、Codex/Provider 兼容性测试生成、回归聚类和 Release Notes 草稿。输入不含凭证或私密对话；输出只作建议，不自动合并、发布、联网或执行不可信贡献代码，并记录使用及采纳情况。

**Why**: It names bounded maintenance jobs and explicit human-control gates.

### 3. Anything else we should know?

**Recommended English (481/500 characters)**

This is an unofficial Alpha project, not affiliated with OpenAI or DeepSeek. Its attack surface includes untrusted provider URLs and handoff text, prompt injection, child-process credentials, shell/network/file access, SQLite/JSONL migration, and third-party CI or code contributions. Codex Security would help review changes across those paths. It does not share subscription quota, decrypt reasoning, or promise same-thread continuation; external providers are billed separately.

**中文翻译**

这是与 OpenAI、DeepSeek 均无隶属关系的非官方 Alpha 项目。真实攻击面包括不可信 Provider URL 和接力文本、Prompt Injection、子进程凭证、Shell/网络/文件访问、SQLite/JSONL 迁移以及第三方 CI 或代码贡献；Codex Security 可帮助评审这些路径上的改动。项目不共享订阅额度、不解密推理内容，也不承诺原线程续聊，外部 Provider 独立计费。

**Why**: It states concrete security paths and preserves accurate product boundaries.

## Most recommended submission version

This section remains withheld until the public repository resolves and live metrics are available. The renderer will generate three current form answers with no placeholders and the exact fixed selections listed above.
