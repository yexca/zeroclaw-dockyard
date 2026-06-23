# Migration From `.env` And Static Compose Agents

The WebUI manager can coexist with the legacy `.env` and static
`agent1`/`agent2`/`agent3` Compose services. Migration does not delete old
files or remove old services.

## Generate Local Manager Config

```powershell
python tools\migrate-env-to-manager.py --env .env
```

This writes:

- `config/manager.local.yaml`
- `config/secrets.local.yaml`

The command refuses to overwrite existing output. Use `--force` only when you
intend to regenerate those migration files.

## Review And Activate

Review generated warnings and YAML files. Then either copy them into the active
paths or point the manager environment at them:

```powershell
Copy-Item config\manager.local.yaml config\manager.yaml
Copy-Item config\secrets.local.yaml config\secrets.yaml
docker compose up -d manager
```

Open `http://127.0.0.1:7652`, validate agents, and start one agent at a time.

## What Is Migrated

The migration tool preserves as much as possible from `.env`:

- agent ports;
- model provider family, alias, model, base URL, wire API, timeout, kind;
- model API keys;
- Matrix homeserver, rooms, user IDs, device IDs, tokens, passwords, recovery
  keys, peers;
- MCP profile and per-agent gateway tokens;
- vision settings;
- heartbeat, pacing, and shell timeout settings;
- proactive sidecar settings under the secrets output for review.

Fields that are empty or ambiguous produce warnings.

## Manual Troubleshooting Path

Static Compose services are kept intentionally. You can still run:

```powershell
docker compose up -d agent1 agent2 agent3
```

Use this path if you need to compare legacy behavior against manager-created
containers during migration.
