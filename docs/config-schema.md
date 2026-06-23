# Manager Configuration Schema

Primary config is YAML. The manager reads `config/manager.yaml` locally, or
`config/manager.example.yaml` if the local file does not exist. Secrets live in
`config/secrets.yaml` and are not committed.

## Top-Level Keys

- `version`: schema version, currently `1`.
- `webui`: default UI language and theme.
- `server`: local WebUI bind host and host port.
- `docker`: Docker API proxy URL, Compose project name, control network,
  runtime network, and Matrix host IP.
- `paths`: container paths plus optional host paths for Docker bind mounts.
- `defaults`: shared image and Matrix defaults.
- `vision`: shared vision model route.
- `heartbeat`: built-in ZeroClaw heartbeat settings.
- `pacing`: loop detection settings.
- `runtime`: shell/tool timeout settings.
- `profiles.llm`: reusable LLM provider profiles.
- `profiles.matrix`: reusable Matrix profiles.
- `profiles.mcp`: reusable MCP profiles.
- `prompt_templates`: reusable workspace prompt files.
- `agents`: per-agent definitions.

## Agent Fields

Common agent fields:

- `id` or `name`: unique identifier.
- `enabled`: UI/runtime intent.
- `host_port`: loopback gateway port.
- `image`: optional image override.
- `llm_profile`, `matrix_profile`, `mcp_profile`: profile references.
- `prompt_template`: workspace template reference.
- `matrix`: per-agent Matrix identity and peer overrides.
- `environment`: explicit environment overrides for advanced use.
- `allow_empty_external_peers`: bypasses peer validation for local testing.

## Secrets

`config/secrets.yaml` may contain plaintext local secrets:

- `vision.api_key`
- `agents.<agent>.model_api_key`
- `agents.<agent>.matrix_access_token`
- `agents.<agent>.matrix_password`
- `agents.<agent>.matrix_recovery_key`
- `agents.<agent>.mcp_gateway_token`

The current manager UI stores secrets inline in the primary config when edited
there. Exports and logs redact secret-like keys by default.

## Validation

Validation checks agent names, duplicate ports, profile references, Matrix
credentials, Matrix peers, workspace writability, server bind address, and
local ignore rules.
