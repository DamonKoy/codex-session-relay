# X/Twitter launch copy

> Ready for manual posting: the repository and v0.1.0 Alpha release are public. Character counts below include the repository URL and use Unicode code-point counts; X may calculate weighted length differently, so verify in the composer before posting. Do not automate publication from this document.

## Recommended bilingual post — 180 characters

Codex Session Relay 开源了：安全切换 Codex 官方登录与 Responses-compatible 外部模型；跨模型接力先脱敏、再确认，目标默认只读。DeepSeek 需经 Responses 网关，额度/计费不共享。Unofficial. https://github.com/DamonKoy/codex-session-relay

## Chinese — 226 characters

我开源了 Codex Session Relay：安全切换 Codex 官方登录与 Responses-compatible 外部模型，并通过“可读消息白名单 → 密钥脱敏 → 人工审阅 → SHA-256 确认 → 默认只读”创建跨模型接力任务。DeepSeek 需要 Responses 网关；订阅与外部 API 的认证、额度和计费始终独立。非官方项目。https://github.com/DamonKoy/codex-session-relay

## English — 259 characters

Codex Session Relay safely uses Codex official auth alongside separately billed providers. Handoffs are allowlisted, redacted, reviewed, SHA-256 confirmed, and read-only by default. Unofficial; no quota sharing. https://github.com/DamonKoy/codex-session-relay

## Three-post thread

1. I built Codex Session Relay to safely use Codex official authentication alongside separately billed Responses-compatible providers while keeping Relay-created tasks visible in one local history bucket.

   Direct DeepSeek API is not presented as Responses-compatible: current Codex requires `/responses`, so DeepSeek needs an explicit compatible gateway.

2. Cross-provider continuation creates a new task. It extracts only readable user/assistant text, excludes reasoning/tools/system instructions, redacts likely secrets, flags prompt injection, requires SHA-256 confirmation, and defaults to read-only.

3. It does not transfer subscription quota, decrypt reasoning, or merge billing/authentication. v0.1.0 is macOS-first, Apache-2.0, standard-library Python, with reversible migration and deterministic builds. https://github.com/DamonKoy/codex-session-relay
