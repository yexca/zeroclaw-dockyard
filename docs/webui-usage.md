# WebUI Usage

The WebUI manager is the only control plane.

## Start

```powershell
Copy-Item config\manager.example.yaml config\manager.yaml
Copy-Item config\secrets.example.yaml config\secrets.yaml
docker compose up -d
```

Open `http://127.0.0.1:7652`.

`docker compose up -d` starts only `manager` and `docker-socket-proxy`. No
agent containers start until the WebUI creates them.

## Main Workflows

- Dashboard: view state, Docker details, logs, config hash, rebuild status, and
  operation history.
- Agents: create, edit, validate, start, stop, restart, delete, export, and
  apply prompt templates.
- Profiles: edit reusable LLM, Matrix, and MCP profiles.
- Prompt templates: edit workspace files that can be applied to agents.
- Export: write redacted generated configuration under `config/generated/`.

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

## Troubleshooting

- If Docker API calls fail, check `docker-socket-proxy` is running.
- If managed containers fail to start, validate the agent in the WebUI first.
- If bind mounts fail, check that `./bootstrap` and `./instances` are mounted
  into the manager service and that the manager can inspect itself through the
  socket proxy.
- Use dashboard logs and operation history for runtime diagnosis.
