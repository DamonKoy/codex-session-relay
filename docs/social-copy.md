# X/Twitter launch copy

> Ready for manual posting: the v0.3.0 prerelease is public and its anonymous installer verification passed. Character counts use Unicode code points; verify X's weighted length manually. Do not automate publication.

## Recommended v0.3.0 post

Codex Session Relay v0.3.0：DeepSeek V4 Flash 已通过官方 Responses API 直连 Codex。安装后运行 `codex-model gpt` / `codex-model deepseek` 即可按次切换；外部 Key 存 Keychain，订阅与计费不共享。Unofficial. https://github.com/DamonKoy/codex-session-relay

## Recommended bilingual post — 180 characters

Codex Session Relay：安全切换 Codex 官方登录与 DeepSeek V4 Flash 官方 Responses API；跨模型接力先脱敏、再确认，目标默认只读。认证、额度和计费不共享。Unofficial. https://github.com/DamonKoy/codex-session-relay

## Chinese — 226 characters

Codex Session Relay v0.3.0 支持通过官方 Responses API 直接使用 DeepSeek V4 Flash，并通过“可读消息白名单 → 密钥脱敏 → 人工审阅 → SHA-256 确认 → 默认只读”创建跨模型接力任务。Codex 订阅与 DeepSeek API 的认证、额度和计费始终独立。非官方项目。https://github.com/DamonKoy/codex-session-relay

## English — 259 characters

Codex Session Relay safely uses Codex official auth alongside separately billed providers. Handoffs are allowlisted, redacted, reviewed, SHA-256 confirmed, and read-only by default. Unofficial; no quota sharing. https://github.com/DamonKoy/codex-session-relay

## Three-post thread

1. I built Codex Session Relay to safely use Codex official authentication alongside separately billed Responses-compatible providers while keeping Relay-created tasks visible in one local history bucket.

   v0.3.0 adds direct DeepSeek V4 Flash support through DeepSeek's official Responses API and a versioned Codex model catalog.

2. Cross-provider continuation creates a new task. It extracts only readable user/assistant text, excludes reasoning/tools/system instructions, redacts likely secrets, flags prompt injection, requires SHA-256 confirmation, and defaults to read-only.

3. It does not transfer subscription quota, decrypt reasoning, or merge billing/authentication. v0.3.0 is macOS-first, Apache-2.0, standard-library Python, with reversible migration and deterministic builds. https://github.com/DamonKoy/codex-session-relay
