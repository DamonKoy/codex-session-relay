# Codex for Open Source application

> Public launch snapshot generated from GitHub data on 2026-08-12. Metrics can change; immediately before submission run `codex-relay application render --repo DamonKoy/codex-session-relay --role creator` and use the newly generated file.

## Verified repository analysis

1. **Purpose**: Safely run Codex with official authentication and separately authenticated Responses-compatible providers, then create reviewed cross-provider handoffs.
2. **Public metrics at launch**: 1 star, 0 forks, and 1 public contributor.
3. **Components**: Provider/key management, runtime launcher, session audit/migration/rollback, title tagging, safe handoff packages, application renderer, tests, and release tooling.
4. **Users**: Codex users and open-source maintainers who need multiple providers without merging credentials or trusting raw transcripts.
5. **Ecosystem value**: A local-first, reversible reference workflow for Provider isolation and explicit human review at Agent trust boundaries.
6. **Agent/tooling scope**: AI Agents, CLI configuration, Keychain, SQLite/JSONL migration, subprocess execution, network Providers, and third-party contributions.
7. **Security risks**: Malicious code/configuration, Prompt Injection, credential leaks, unauthorized requests, filesystem/session corruption, dependency or release compromise, and risky contributions.
8. **Codex Security fit**: Review data-flow and execution paths that cross transcript, credential, Provider, Shell, network, and filesystem boundaries.
9. **API credit use**: Redacted Issue triage, PR risk review, compatibility tests, regression analysis, and draft Release Notes with maintainer approval.

## Current form mapping

- **GitHub username**: `DamonKoy`
- **GitHub repository URL**: https://github.com/DamonKoy/codex-session-relay
- **Role**: Primary maintainer (Creator maps to this current form option)
- **Interests**: Codex Security; API credits for my project
- **Fill manually and never store in generated files**: first name, last name, ChatGPT account email, and OpenAI Organization ID

## Application fields

### 1. Why does this repository qualify?

**Recommended English (483/500 characters)**

Codex Session Relay is an Apache-2.0 macOS CLI that keeps Codex official authentication separate from external provider keys and creates reviewed, redacted cross-model handoffs. It includes reversible JSONL/SQLite migration, Keychain integration, read-only defaults, tests, and security documentation. GitHub currently reports 1 star, 0 forks, and 1 public contributor. It gives agent-tool users a local-first reference for provider isolation and explicit review at trust boundaries.

**中文翻译**

Codex Session Relay 是 Apache-2.0 的 macOS CLI，将 Codex 官方认证与外部 Provider 密钥隔离，并创建经审阅、脱敏的跨模型接力任务。项目包含可回滚的 JSONL/SQLite 迁移、Keychain 集成、默认只读、安全文档和测试。GitHub 当前公开指标为 1 Star、0 Fork、1 位贡献者，为 Agent 工具用户提供本地优先的 Provider 隔离及信任边界人工复核参考实现。

**Why**: It uses live GitHub metrics and verifiable repository artifacts.

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

### Why does this repository qualify?

Codex Session Relay is an Apache-2.0 macOS CLI that keeps Codex official authentication separate from external provider keys and creates reviewed, redacted cross-model handoffs. It includes reversible JSONL/SQLite migration, Keychain integration, read-only defaults, tests, and security documentation. GitHub currently reports 1 star, 0 forks, and 1 public contributor. It gives agent-tool users a local-first reference for provider isolation and explicit review at trust boundaries.

### How will you use API credits for your project?

Credits will support maintainer-reviewed automation for redacted issue triage, PR risk summaries, compatibility-test generation for Codex/provider changes, regression clustering, and draft release notes. Inputs will exclude credentials and private transcripts. Outputs will be advisory: no automatic merge, release, network action, or execution of untrusted contributor code. Usage and acceptance will be logged for maintainability and abuse review.

### Anything else we should know?

This is an unofficial Alpha project, not affiliated with OpenAI or DeepSeek. Its attack surface includes untrusted provider URLs and handoff text, prompt injection, child-process credentials, shell/network/file access, SQLite/JSONL migration, and third-party CI or code contributions. Codex Security would help review changes across those paths. It does not share subscription quota, decrypt reasoning, or promise same-thread continuation; external providers are billed separately.
