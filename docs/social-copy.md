# X/Twitter launch copy

> Draft only. Do not post until the repository is public and the URL resolves. Character counts below include the intended repository URL and use Unicode code-point counts; X may calculate weighted length differently, so verify in the composer before posting.

## Recommended bilingual post — 249 characters

Codex Session Relay 开源了：在 Codex 官方登录与 DeepSeek 等独立 API 之间安全切换；跨模型接力先脱敏、再确认，目标默认只读。Open source: safe provider switching + reviewed, redacted handoffs for Codex. Unofficial; quotas/billing stay separate. https://github.com/DamonKoy/codex-session-relay

## Chinese — 199 characters

我开源了 Codex Session Relay：在 Codex 官方登录与 DeepSeek 等独立 API 之间安全切换，并通过“可读消息白名单 → 密钥脱敏 → 人工审阅 → SHA-256 确认 → 默认只读”的流程创建跨模型接力任务。订阅与外部 API 的认证、额度和计费始终独立。非官方项目。https://github.com/DamonKoy/codex-session-relay

## English — 259 characters

Codex Session Relay safely uses Codex official auth alongside separately billed providers. Handoffs are allowlisted, redacted, reviewed, SHA-256 confirmed, and read-only by default. Unofficial; no quota sharing. https://github.com/DamonKoy/codex-session-relay

## Three-post thread

1. I built Codex Session Relay to safely use Codex official authentication alongside separately billed Responses-compatible providers while keeping Relay-created tasks visible in one local history bucket.

2. Cross-provider continuation creates a new task. It extracts only readable user/assistant text, excludes reasoning/tools/system instructions, redacts likely secrets, flags prompt injection, requires SHA-256 confirmation, and defaults to read-only.

3. It does not transfer subscription quota, decrypt reasoning, or merge billing/authentication. v0.1.0 is macOS-first, Apache-2.0, standard-library Python, with reversible migration and deterministic builds. https://github.com/DamonKoy/codex-session-relay

