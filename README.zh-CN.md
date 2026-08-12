# Codex Session Relay

Codex Session Relay 是一个本地优先的 macOS CLI，用于在 Codex 官方认证和独立认证的 Responses-compatible 外部模型之间安全切换，并把两类任务统一显示在同一个本地历史桶中。跨 Provider 时，它不会强行续聊原线程，而是生成一份经人工审阅和脱敏的新任务接力包。

> **非官方项目，与 OpenAI 或 DeepSeek 无隶属关系。** Codex 订阅与外部 Provider API 的认证、额度、计费和信任边界完全独立。本项目不转移 GPT 订阅额度、不解密推理内容，也不承诺跨 Provider 原线程续聊。

## 主要能力

- OpenAI 模式沿用 Codex 官方登录态，不读取或复制认证内容。
- 外部 Provider 的 API Key 保存在 macOS Keychain，只通过子进程环境注入。
- Relay 启动的 Provider 共用 `custom` 历史桶，同时保留真实模型名称。
- 会话审计只读；归一迁移和标题标记必须经过计划文件及 SHA-256 确认。
- 迁移前备份 SQLite 与原始 JSONL 首行，迁移后验证会话正文 tail 完全不变。
- 接力只允许用户/助手可读消息，排除 system/developer、reasoning、密文和工具记录。
- 接力包会做秘密脱敏、Prompt Injection 风险提示，并在编辑后重新扫描。
- 目标 Codex 默认使用 `read-only`，写权限必须显式选择。

## 快速开始

```bash
python3 -m pip install --user .
codex-relay doctor
codex-relay provider list
codex-relay key set deepseek
codex-relay run deepseek -- -C "$PWD"
```

OpenAI 官方认证模式：

```bash
codex-relay run openai -- -C "$PWD"
```

DeepSeek 使用独立 API Key 和独立计费：

```bash
codex-relay key status deepseek
codex-relay run deepseek -- -C "$PWD"
```

## 会话归一

```bash
codex-relay history audit
codex-relay history plan-normalize --output /tmp/relay-plan.json
codex-relay history apply-normalize --plan /tmp/relay-plan.json --confirm <sha256>
```

执行写入前必须退出 Codex/ChatGPT。计划生成后，如果 Codex 版本、数据库结构或目标会话发生变化，工具会拒绝执行。

## 跨模型接力

```bash
codex-relay handoff prepare <任务ID> --to deepseek
codex-relay handoff show <接力包目录>
codex-relay handoff send <接力包目录> --confirm <当前摘要>
```

发送内容通过 stdin 进入目标 Codex，不放入进程参数；映射日志只记录任务 ID、Provider、模型、摘要和沙箱，不记录接力正文或密钥。

更完整的架构、安全、运维和扩展说明见 [docs](docs/)。

