# ZeroClaw Multi Docker

Local WebUI manager for creating and operating multiple ZeroClaw Matrix agents
from one Docker Compose project.

The manager is the only default entrypoint. A plain `docker compose up -d`
starts the WebUI and Docker socket proxy; agent containers are created,
configured, started, stopped, and deleted by the WebUI through the Docker API.

Chinese documentation is available in [README.zh-cn.md](README.zh-cn.md).

## What Is Included

- `docker-compose.yml`: WebUI manager and Docker socket proxy.
- `.env.example`: optional overrides for WebUI/proxy startup.
- `config/manager.example.yaml`: structured manager configuration.
- `config/secrets.example.yaml`: local plaintext secrets template.
- `manager/`: WebUI backend and frontend.
- `bootstrap/render-config.sh`: rendered into manager-created agent containers.
- `templates/workspace/`: starter workspace prompt files.

## Start

```powershell
Copy-Item config\manager.example.yaml config\manager.yaml
Copy-Item config\secrets.example.yaml config\secrets.yaml
docker compose up -d
```

Open `http://127.0.0.1:7652`.

The manager binds to `127.0.0.1` and reaches Docker through
`docker-socket-proxy`. The manager container does not mount
`/var/run/docker.sock` directly.

## Configure Agents

Use the WebUI to edit:

- LLM profiles
- Matrix profiles
- MCP profiles
- prompt templates
- per-agent ports, identities, model/profile assignments, and secrets

The dashboard shows runtime status, logs, config hashes, rebuild status, and
operation history.

Detailed docs:

- [WebUI usage](docs/webui-usage.md)
- [Configuration schema](docs/config-schema.md)
- [Docker socket proxy security](docs/docker-socket-proxy-security.md)
- [i18n and theme](docs/i18n-theme.md)
- [Architecture](docs/webui-architecture.md)

## Image

Manager-created agents use:

```env
ZEROCLAW_IMAGE=ghcr.io/zeroclaw-labs/zeroclaw:v0.8.1-debian
```

Override it in `.env`, `config/manager.yaml`, or per-agent config.

## Keep Secrets Out Of Git

Do not commit:

- `.env`
- `config/manager.yaml`
- `config/secrets.yaml`
- `config/manager.local.yaml`
- `config/secrets.local.yaml`
- `config/generated/*`
- `instances/*`

The included `.gitignore` covers these paths.

## Tests And Release Checks

Run the full local release check:

```powershell
.\tools\release-checks.ps1
```

Individual checks:

```powershell
docker compose config --quiet
python -m unittest discover manager/backend/tests
node manager/frontend/tests/ui-foundation.test.mjs
```
