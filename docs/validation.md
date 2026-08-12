# 验证状态 / Validation status

更新日期：2026-08-13。本文件区分“本机真实只读/无副作用验证”“隔离自动化测试”和“尚未验证”，避免把单机结果描述为所有 Mac 通用。

## 当前基线

- macOS 15.7.8，Apple silicon
- Python 3.9.13
- Codex CLI 0.147.0
- 真实 `state_5.sqlite`：443 个任务，文件与索引 Provider 一致
- GitHub Actions：`macos-15` ARM64 / Python 3.13 与 `macos-15-intel` / Python 3.9，49 项测试及双次可复现构建通过（[run 31616826581](https://github.com/DamonKoy/codex-session-relay/actions/runs/31616826581)）

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
| DeepSeek 官方 Responses 地址 | 官方文档 + Codex 0.147.0 使用无效测试 Key 的无状态请求 | Codex 请求到达 `https://api.deepseek.com/responses` 并收到预期 401；未读取或使用真实 Key |
| DeepSeek V4 模型目录 | 官方目录字段 + 本机 Codex 0.147.0 `debug models` | `deepseek-v4-flash` 目录可被当前 Codex 解析；最低版本固定为 0.144.0 |
| DeepSeek 认证调用 | 配置、Keychain 注入和失败关闭测试 | 尚未完成真实模型响应、工具调用与流式事件验证；需要维护者测试账户 |
| ARM64 与 Intel 自动化路径 | GitHub-hosted `macos-15` / Python 3.13 与 `macos-15-intel` / Python 3.9 | v0.3.0 的 49 项测试、字段长度、可复现构建、校验和与两个 ZipApp 入口冒烟通过（[run 31616826581](https://github.com/DamonKoy/codex-session-relay/actions/runs/31616826581)） |
| `codex-model` 快捷启动 | 临时配置 + 假 Codex | GPT/DeepSeek 路由、项目路径、参数透传、首次配置失败关闭通过；真实外部网络仍未调用 |
| 一键安装 | 匿名公开下载 + 临时安装目录 | v0.3.0 Release 两项资产 SHA-256 通过且与本地构建逐字节一致；两个入口均报告 0.3.0，状态显示官方 DeepSeek 地址且未读取真实 Key |
| 其他 macOS/Codex 版本 | 未覆盖 | 不得宣称已验证；不兼容 schema 会失败关闭 |

## 发布前仍需人工验证

1. 在普通 macOS Terminal（登录钥匙串已解锁）使用一次性测试值执行 `key set → key status → 删除测试项`。
2. 使用 DeepSeek 测试账户调用官方 `/responses`，验证模型响应、工具调用、流式事件和错误处理。
3. 在复制的 Codex 数据目录上做迁移/回滚演练；不要以真实主会话作为首次写入测试。

因此，当前可以称为“DeepSeek 官方 Responses 端点与模型目录兼容性已核验，密钥安全注入已自动化验证”。不能称为“所有 Mac 通用”“所有 Codex 版本兼容”“Keychain 真实写入闭环已验证”或“DeepSeek 认证端到端已验证”。
