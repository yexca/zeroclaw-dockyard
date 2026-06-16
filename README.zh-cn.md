# ZeroClaw Multi Docker

用于在一台主机上运行多个 ZeroClaw Matrix agent 的 Docker Compose 模板。

本项目面向 ZeroClaw `0.8.0-beta-2`，提供可复现的容器配置：Matrix
channel、多 agent 独立 workspace、每个 agent 独立模型 provider、可选视觉路由、
可选 MCP gateway，以及可选 proactive 唤醒 sidecar。

英文文档见 [README.md](README.md)。

## 包含内容

- `docker-compose.yml`: 默认包含 `agent1`、`agent2`、`agent3` 三个示例 agent，以及可选 proactive sidecar。
- `Dockerfile`: 在 Matrix 版 ZeroClaw 镜像上添加常用诊断工具。
- `.env.example`: 模型、Matrix 账号、MCP、proactive 唤醒相关的公开占位配置。
- `bootstrap/render-config.sh`: 在容器启动时渲染 ZeroClaw schema v3 `config.toml`。
- `proactive/proactive.py`: 可选 sidecar，定时向每个 agent gateway POST 唤醒 prompt。
- `tools/add-agent.ps1`: 用于添加更多 agent service 的 PowerShell 辅助脚本。
- `tools/reset-agent-state.ps1`: 用于清理生成态并轮换 Matrix device ID 的辅助脚本。
- `templates/workspace/`: 每个 agent workspace 的空白指令和记忆模板。
- `patches/zeroclaw-0.8.0-beta2-docker-matrix.patch`: 用于构建 Matrix 版 Docker 镜像的补丁。

## 构建基础镜像

上游版本是 `0.8.0-beta-2`。本仓库补丁基于 ZeroClaw 提交
`af50475a37fa9d2ae78758d2fbe82bda67218c17` 生成，该提交的 Cargo package
版本仍是 `0.8.0-beta-2`。

```powershell
git clone https://github.com/zeroclaw-labs/zeroclaw.git
cd zeroclaw
git checkout af50475a37fa9d2ae78758d2fbe82bda67218c17
git apply ..\zeroclaw_multi_docker\patches\zeroclaw-0.8.0-beta2-docker-matrix.patch
docker build -f Dockerfile.debian -t zeroclaw:0.8.0-beta2-matrix .
```

## 构建工具层镜像

Compose 可以在基础镜像上构建一层很薄的工具层：

```powershell
cd zeroclaw_multi_docker
docker compose build
```

工具层包含 `bash`、`curl`、`file`、`jq`、`less`、`nano`、`ping`、`ss`/`ip`、
`vim`、`xxd`、`zip`、`unzip` 等命令。若希望 agent 容器里也有
`python`、`python3`、`pip3` 和 venv，重建前设置
`ZEROCLAW_INSTALL_PYTHON3=true`。

## 配置

```powershell
cd zeroclaw_multi_docker
Copy-Item .env.example .env
```

编辑 `.env`，至少填写：

- `MATRIX_HOMESERVER`
- `AGENT*_MATRIX_USER_ID`
- `AGENT*_MATRIX_PASSWORD` 或 `AGENT*_MATRIX_ACCESS_TOKEN`
- `AGENT*_MATRIX_RECOVERY_KEY`，如果使用 Matrix E2EE。
- `AGENT*_MATRIX_EXTERNAL_PEERS`，包含允许给 agent 发消息的用户 MXID，以及出站房间目标。
- `AGENT*_MODEL_*`，或保留示例中的 DeepSeek、Ollama、Gemini 默认值。
- `VISION_API_KEY`，如果需要把 Matrix 图片消息路由到视觉模型。

初始化 workspace 文件：

```powershell
New-Item -ItemType Directory -Force instances\agent1\workspace,instances\agent2\workspace,instances\agent3\workspace
Copy-Item templates\workspace\* instances\agent1\workspace\
Copy-Item templates\workspace\* instances\agent2\workspace\
Copy-Item templates\workspace\* instances\agent3\workspace\
```

## 运行

```powershell
docker compose up -d agent1 agent2 agent3
```

默认 gateway 端口只绑定 localhost：

- agent1: `http://127.0.0.1:42641`
- agent2: `http://127.0.0.1:42642`
- agent3: `http://127.0.0.1:42643`

## 每 Agent 独立模型 Provider

每个 agent 的 `AGENT*_MODEL_*` 会被 Compose 映射到容器内通用变量，再由
`bootstrap/render-config.sh` 写入单独的 provider block，并把
`agents.main.model_provider` 指向该 provider。

示例 `.env`：

```env
AGENT1_MODEL_PROVIDER_FAMILY=deepseek
AGENT1_MODEL_PROVIDER_ALIAS=text
AGENT1_MODEL=deepseek-chat
AGENT1_MODEL_BASE_URL=https://api.deepseek.com/v1
AGENT1_MODEL_API_KEY=
AGENT1_MODEL_WIRE_API=chat_completions
AGENT1_MODEL_TIMEOUT_SECS=120

AGENT2_MODEL_PROVIDER_FAMILY=ollama
AGENT2_MODEL_PROVIDER_ALIAS=local
AGENT2_MODEL=qwen2.5:14b
AGENT2_MODEL_BASE_URL=http://host.docker.internal:11434
AGENT2_MODEL_API_KEY=
AGENT2_MODEL_WIRE_API=chat_completions
AGENT2_MODEL_TIMEOUT_SECS=600

AGENT3_MODEL_PROVIDER_FAMILY=gemini
AGENT3_MODEL_PROVIDER_ALIAS=flash
AGENT3_MODEL=gemini-2.5-flash
AGENT3_MODEL_BASE_URL=
AGENT3_MODEL_API_KEY=
AGENT3_MODEL_WIRE_API=
AGENT3_MODEL_TIMEOUT_SECS=120
```

`MODEL_PROVIDER_FAMILY` 和 `MODEL_PROVIDER_ALIAS` 会组成 dotted provider
引用，例如 `ollama.local`、`deepseek.text`、`openai.main`、`gemini.flash`。

视觉路由仍使用名为 `vision` 的 v3 `model_routes`，并指向 `custom.vision`。
包含 Matrix 图片标记（`[IMAGE:` / `[Image:`）的消息会被路由到该视觉模型。

## MCP Gateway

每个 agent 可以给宿主机 MCP gateway 使用不同 bearer token：

```env
AGENT1_MCP_GATEWAY_TOKEN=agent1-token
AGENT2_MCP_GATEWAY_TOKEN=agent2-token
AGENT3_MCP_GATEWAY_TOKEN=agent3-token
```

Compose 会把每个值映射进对应容器的 `MCP_GATEWAY_TOKEN`。共享的
`MCP_GATEWAY_TOKEN` 只在 agent 专属值为空时作为 fallback。

## 输入 Debounce 和 Shell 超时

默认 `CHANNEL_DEBOUNCE_MS=3000` 会渲染为 `[channels].debounce_ms = 3000`。
同一发送者/会话在短时间内连续发送的消息会在 3 秒静默窗口后合并为一次
agent turn。设为 `0` 可关闭入站 debounce。

Shell 执行限制由这些变量配置：

```env
SHELL_TIMEOUT_SECS=300
SHELL_TOOL_TIMEOUT_SECS=300
```

## 添加更多 Agent

```powershell
.\tools\add-agent.ps1 -Id 4 -ProviderFamily ollama -ProviderAlias local -Model "qwen2.5:14b"
```

脚本会创建 `instances/agent4/workspace`，向 `.env` 追加 `AGENT4_MODEL_*`、
Matrix 和 `AGENT4_MCP_GATEWAY_TOKEN` 变量，向 `docker-compose.yml` 插入
`agent4` service，并把该 service 加入 proactive sidecar 依赖。

常用参数：

- `-HostPort 42644` 指定 localhost gateway 端口。
- `-MatrixUserId "@agent4:matrix.example.com"` 预填 Matrix 用户 ID。
- `-ExternalPeers "@you:matrix.example.com,#agent4-room:matrix.example.com"` 预填 peer gate。
- `-ProactiveTarget "#agent4-room:matrix.example.com"` 添加 proactive 目标映射。
- `-ProviderFamily ollama|deepseek|openai|gemini` 选择 provider family。
- `-ProviderAlias local` 选择 `ollama.local` 中的 alias 段。
- `-Model "qwen2.5:14b"` 设置发送给 provider 的模型名。
- `-BaseUrl "http://host.docker.internal:11434"` 覆盖 provider endpoint。
- `-ApiKey "sk-..."` 在需要时设置 provider key。
- `-WireApi chat_completions` 设置 OpenAI-compatible chat completions。
- `-DryRun` 预览文件和配置改动。

## 重置 Agent 状态

需要清理 ZeroClaw 生成态、但保留 workspace 文件时，可以使用：

```powershell
.\tools\reset-agent-state.ps1 -Agent agent1 -DryRun
.\tools\reset-agent-state.ps1 -Agent agent1
```

该脚本会删除生成的 config/state 目录，并在 `.env` 中轮换所选 agent 的
`AGENT*_MATRIX_DEVICE_ID`。

## Proactive Sidecar

sidecar 默认关闭。启用时设置：

```dotenv
PROACTIVE_ENABLED=true
PROACTIVE_TARGETS=agent1=#agent1-room:matrix.example.com,agent2=#agent2-room:matrix.example.com,agent3=#agent3-room:matrix.example.com
```

然后启动：

```powershell
docker compose up -d proactive
```

sidecar 会以随机间隔向每个已配置 agent 的 `/webhook` 发送唤醒请求。是否发送
Matrix 出站消息由 agent 自己决定。

## 不要提交敏感信息

不要提交：

- `.env`
- `instances/*/.zeroclaw/`
- `instances/*/data/`
- `instances/*/workspace/sessions/`
- SQLite 数据库、Matrix crypto store、socket、日志、备份、生成媒体，以及本地 workspace 文件
- `proactive/state/`

仓库内 `.gitignore` 已覆盖这些路径。发布前建议运行：

```powershell
rg -n "api[_-]?key|token|password|recovery|secret|PRIVATE KEY|Bearer " .
```
