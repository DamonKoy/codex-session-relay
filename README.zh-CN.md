# Codex Session Relay

[![CI](https://github.com/DamonKoy/codex-session-relay/actions/workflows/ci.yml/badge.svg)](https://github.com/DamonKoy/codex-session-relay/actions/workflows/ci.yml)

Codex Session Relay 是一个本地优先的 macOS 命令行工具。它让你在同一个 Codex 项目里安全地使用 OpenAI 官方登录和 DeepSeek 等外部模型，并把已经审阅、脱敏的对话上下文接力到一个新任务。

> **非官方项目，与 OpenAI 或 DeepSeek 无隶属关系。** OpenAI 模式沿用 Codex 官方订阅登录；DeepSeek 等外部模型使用各自的 API Key、额度和计费。Relay 不共享订阅额度、不读取 `auth.json` 内容、不解密推理，也不保证跨 Provider 在原线程续聊。

## 一分钟开始

要求：macOS、Python 3.9+，并已安装或运行过 Codex CLI/桌面版。

```bash
curl -fsSL https://raw.githubusercontent.com/DamonKoy/codex-session-relay/main/install.sh | sh
```

新开终端，在任意项目目录运行：

```bash
codex-model gpt
codex-model deepseek
```

- `gpt` 使用已有 Codex 官方登录态，不读取或复制 `auth.json`。
- `deepseek` 首次运行会询问 Responses-compatible HTTPS 网关，并以无回显方式把 Key 保存到 macOS Keychain；以后可直接启动。
- 指定项目：`codex-model gpt /path/to/project`。
- 传递 Codex 参数：`codex-model deepseek -- --sandbox read-only`。
- 查看状态：`codex-model status`；接力、迁移等完整功能仍使用 `codex-relay`。

这里的“切换”是为本次启动选择 Provider，不会永久改写 `~/.codex/config.toml`。DeepSeek 官方公开接口目前是 Chat Completions/Anthropic 格式，不是 Codex 所需的 Responses 接口，因此仍需要自有或组织的 `/responses` 网关。

## 先选择你要做什么

| 目标 | 最短路径 | 是否修改历史数据 |
| --- | --- | --- |
| 用 OpenAI 启动 Codex | `codex-model gpt` | 否 |
| 经 Responses 网关使用 DeepSeek | `codex-model deepseek`（首次自动配置） | 否 |
| 把最近任务接力给另一个模型 | `handoff prepare --last` → 审阅 → `show` → `send` | 新建任务，不改原任务 |
| 修复侧边栏按 Provider 分组 | `history audit` → `plan-normalize` → `apply-normalize` | 是；有备份和回滚 |

如果只是切换模型或接力任务，不需要执行历史迁移。

## 手动安装与首次检查

要求：macOS、Python 3.9+，并且 Codex CLI 或桌面版已经运行过。项目无第三方运行时依赖。

```bash
cd /path/to/codex-session-relay
python3 -m pip install --user .
codex-relay --version
codex-relay doctor
```

`doctor` 会以“通过 / 待配置 / 错误”显示检查结果。未配置 DeepSeek Responses 网关或 Key 都只是“待配置”，不会妨碍 OpenAI 模式。脚本需要 JSON 时使用：

```bash
codex-relay doctor --json
```

如果安装成功但提示 `command not found: codex-relay`，先找到用户安装目录：

```bash
python3 -m site --user-base
```

把输出目录下的 `bin` 加入 `PATH`。例如输出是 `/Users/me/Library/Python/3.9`：

```bash
echo 'export PATH="$HOME/Library/Python/3.9/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

也可以不安装，直接构建并运行单文件版本：

```bash
python3 scripts/build.py
python3 dist/codex-relay-0.2.0.pyz doctor
(cd dist && shasum -a 256 -c SHA256SUMS)
```

## 使用底层命令启动 OpenAI 或 DeepSeek

OpenAI 使用现有 Codex 官方认证，Relay 不读取或复制认证内容：

```bash
codex-relay run openai -- -C "$PWD"
```

当前 Codex 只支持 Responses wire API，而 DeepSeek 官方公开 API 是 Chat Completions，不能把 `https://api.deepseek.com` 直接填给当前 Codex。你需要一个明确支持 `/responses`、并能路由到 DeepSeek 的自有或组织网关：

```bash
codex-relay provider configure deepseek \
  --base-url https://YOUR_RESPONSES_GATEWAY/v1
codex-relay key set deepseek
codex-relay key status deepseek
codex-relay run deepseek -- -C "$PWD"
```

Relay 不提供或代管该网关。Key 不写入配置、命令参数、日志、接力包或 Git 文件；它只通过目标 Codex 子进程的环境变量注入。外部调用按所配置网关/Provider 的账户独立计费。

想先查看非秘密启动参数，不启动 Codex：

```bash
codex-relay run deepseek --dry-run -- -C "$PWD"
```

## 3. 把任务接力到另一个模型

最简单的方式是接力指定项目最近的任务：

```bash
codex-relay handoff prepare --last --project "$PWD" --to deepseek
```

如果要选择更早的任务，先列出任务并复制 ID：

```bash
codex-relay session list --project "$PWD"
codex-relay handoff prepare <任务ID> --to deepseek
```

`prepare` 只生成本地接力包，不会发送。接下来：

1. 打开命令输出的 `context.md` 和 `risk-report.md`。
2. 删除不想共享的代码、个人信息、内部链接或历史指令。
3. 运行输出提示的 `handoff show`。
4. 再复制 `show` 输出的完整 `handoff send ... --confirm ...` 命令。

`send` 会再次扫描秘密并通过 stdin 发送，默认新任务为 `read-only`。确实需要目标模型修改代码时，才手动添加 `--sandbox workspace-write`。

接力包不会包含 system/developer 指令、reasoning、工具参数、工具输出或 `encrypted_content`。历史文本会被明确标为“不可信数据”，不会作为新系统指令发送。

## 4. 只有侧边栏分组异常时才迁移

先只读检查：

```bash
codex-relay history audit
```

只有审计显示存在可归一任务，并且你确实需要合并侧边栏历史桶时，才继续：

```bash
codex-relay history plan-normalize --output /tmp/relay-plan.json
```

该命令不会修改数据，并会打印带完整 SHA-256 的下一条命令。人工审阅计划、退出 Codex/ChatGPT 后，再复制执行。完成后终端会打印备份目录和完整回滚命令。

Relay 只修改 JSONL 首行的 `session_meta.payload.model_provider` 和 SQLite 对应索引；正文、工具记录及密文不变。版本、schema、文件摘要、活动客户端或确认摘要不匹配时会拒绝执行。

## 常见问题

- **DeepSeek Responses 接口显示“待配置”**：只使用 OpenAI 时可以忽略；需要 DeepSeek 时先配置一个真正支持 `/responses` 的网关，不能使用官方 Chat Completions 地址冒充。
- **DeepSeek API Key 显示“待配置”**：按网关要求设置对应 Key；Relay 不会显示密钥内容。
- **未检测到 Codex 官方认证**：先运行 `codex login` 或在 Codex 桌面版完成登录，再重新运行 `doctor`。
- **找不到任务**：先在 Codex 中运行过一次任务，再用 `session list`；使用 `--project` 时确保路径与任务工作目录一致。
- **摘要不匹配**：文件在生成摘要后有变化；重新运行 `handoff show` 或重新生成迁移计划，不要绕过检查。
- **检测到活动客户端**：退出 Codex 和 ChatGPT 后再执行迁移或回滚。
- **未知 schema/Codex 版本**：不要强行迁移；升级 Relay 或提交兼容性问题。

## 升级与卸载

再次执行一键安装命令即可升级到安装器声明的版本。安装器只接受 HTTPS Release，校验 SHA-256 后才替换文件；默认安装到 `~/.local/bin`，并幂等更新 `~/.zshrc`。如果目标目录已有同名普通文件，会先保留为 `.previous`。

在新源码目录中重新安装即可升级：

```bash
python3 -m pip install --user --upgrade .
```

卸载程序：

```bash
python3 -m pip uninstall codex-session-relay
```

一键安装版可删除 `~/.local/bin/codex-relay` 和 `~/.local/bin/codex-model`。卸载不会自动删除 `~/.codex-session-relay` 或 macOS 钥匙串中的 Key，避免意外破坏用户数据。请确认不再需要后手动清理。

## 安全和开发文档

- [架构与数据流](docs/architecture.md)
- [安全模型、威胁边界与隐私](docs/security-model.md)
- [迁移、接力与故障排查](docs/operations.md)
- [验证状态与未覆盖项](docs/validation.md)
- [扩展路线](docs/roadmap.md)
- [安全报告](SECURITY.md)
- [贡献指南](CONTRIBUTING.md)
- [Git 与发布流程](docs/git-release.md)

Apache-2.0，详见 [LICENSE](LICENSE)。
