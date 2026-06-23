# WebUI Usage

The WebUI manager is the preferred control plane for new ZeroClaw multi-agent
setups. It runs locally and binds to `127.0.0.1`.

## Start

```powershell
Copy-Item config\manager.example.yaml config\manager.yaml
Copy-Item config\secrets.example.yaml config\secrets.yaml
$env:PWD = (Get-Location).Path
docker compose up -d manager
```

Open `http://127.0.0.1:7652`.

The legacy static services remain available:

```powershell
docker compose up -d agent1 agent2 agent3
```

## Main Workflows

- Dashboard: view each agent state, Docker details, recent logs, config hash,
  rebuild status, and operation history.
- Agents: create, edit, validate, start, stop, restart, delete, export, and
  apply prompt templates.
- Profiles: edit reusable LLM, Matrix, and MCP profiles.
- Prompt templates: edit workspace files that can be applied to agents.
- Export: write redacted, reviewable generated configuration under
  `config/generated/`.

## Files

Commit examples only:

- `config/manager.example.yaml`
- `config/secrets.example.yaml`

Do not commit local/runtime files:

- `config/manager.yaml`
- `config/secrets.yaml`
- `config/manager.local.yaml`
- `config/secrets.local.yaml`
- `config/generated/*`
- `instances/*`
- `proactive/state/*`

## Troubleshooting

- If Docker API calls fail, check `docker-socket-proxy` is running.
- If managed containers fail to start, validate the agent in the WebUI first.
- If bind mounts fail, set `HOST_PROJECT_DIR` in `.env` to the absolute host
  repository path and restart `manager`.
- Use the static Compose agents for manual troubleshooting while migrating.
