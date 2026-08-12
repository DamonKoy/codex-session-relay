# 验证状态 / Validation status

更新日期：2026-08-12。本文件区分“本机真实只读/无副作用验证”“隔离自动化测试”和“尚未验证”，避免把单机结果描述为所有 Mac 通用。

## 当前基线

- macOS 15.7.8，Apple silicon
- Python 3.9.13
- Codex CLI 0.147.0-alpha.6.5
- 真实 `state_5.sqlite`：443 个任务，文件与索引 Provider 一致
- GitHub Actions：`macos-15` ARM64 / Python 3.13 与 `macos-15-intel` / Python 3.9，34 项测试及双次可复现构建通过（[run 31590308585](https://github.com/DamonKoy/codex-session-relay/actions/runs/31590308585)）

## 验证矩阵

| 能力 | 验证方式 | 当前结论 |
| --- | --- | --- |
| `doctor`、Codex 版本和 schema 检查 | 当前 Mac + 真实 Codex 数据 | 通过 |
| `session list` 与长标题处理 | 当前 Mac 真实任务 + 隔离测试 | 通过 |
| OpenAI 启动参数 | 当前 Mac `--dry-run` | 通过；未新建外部任务 |
| Keychain 缺失项读取 | 当前 Mac 真实 Keychain 命令 | 通过；首次使用显示“待配置” |
| Keychain 写入/读取/删除 | 伪终端实现 + 隔离测试；当前 Codex 执行会话尝试真实写入 | 代码测试通过，但当前执行会话无法获得登录钥匙串授权（`security=152`/超时），尚未完成真实闭环 |
| 历史审计 | 当前 Mac 真实数据，只读 | 通过；443/443 一致，无需迁移 |
| 迁移、回滚、锁、损坏备份 | 临时 SQLite/JSONL | 通过；未修改真实会话 |
| 接力提取、脱敏、确认、只读发送参数 | 临时会话 + 假 Codex | 通过；未发送真实会话 |
| DeepSeek 官方直连 | 官方接口与当前 Codex 协议核验 | 不支持：当前 Codex 要求 Responses，DeepSeek 官方公开 API 是 Chat Completions |
| 经 Responses 网关调用 DeepSeek | 配置和失败关闭测试 | 尚未完成真实网络调用；需要用户自有网关和测试 Key |
| ARM64 与 Intel 自动化路径 | GitHub-hosted `macos-15` / Python 3.13 与 `macos-15-intel` / Python 3.9 | v0.1.0 的 35 项测试、字段长度、可复现构建、校验和与 ZipApp 冒烟通过；v0.2.0 合并前以本地隔离测试为准，发布后补 CI run |
| `codex-model` 快捷启动 | 临时配置 + 假 Codex | GPT/DeepSeek 路由、项目路径、参数透传、首次配置失败关闭通过；真实外部网络仍未调用 |
| 一键安装 | 本地 Release 资产 + 临时 HOME/安装目录 | SHA-256 校验、两个入口、版本冒烟与非 HTTPS 拒绝通过；公开 v0.2.0 Release URL 待发布后验证 |
| 其他 macOS/Codex 版本 | 未覆盖 | 不得宣称已验证；不兼容 schema 会失败关闭 |

## 发布前仍需人工验证

1. 在普通 macOS Terminal（登录钥匙串已解锁）使用一次性测试值执行 `key set → key status → 删除测试项`。
2. 使用测试账户连接一个真实 `/responses` 网关，验证模型响应、工具调用、流式事件和错误处理。
3. 在复制的 Codex 数据目录上做迁移/回滚演练；不要以真实主会话作为首次写入测试。

因此，当前可以称为“Apple silicon 本机只读基线，以及 ARM64/Intel macOS 15 自动化安全路径已验证”；`codex-model` 和安装器已有隔离测试，但在 v0.2.0 公共 CI/Release 完成前仍是候选功能。不能称为“所有 Mac 通用”“所有 Codex 版本兼容”或“DeepSeek 端到端已验证”。
