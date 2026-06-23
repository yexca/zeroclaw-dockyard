#!/usr/bin/env python3
"""Migrate legacy .env agent settings into manager YAML files."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml


DEFAULT_AGENTS = ("1", "2", "3")


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = unquote_env(value.strip())
    return values


def unquote_env(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    return value.replace(r"\n", "\n")


def bool_value(value: str | None, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def int_value(value: str | None, default: int) -> int:
    try:
        return int(value or default)
    except ValueError:
        return default


def list_value(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def first(values: dict[str, str], *keys: str, default: str = "") -> str:
    for key in keys:
        if values.get(key, "") != "":
            return values[key]
    return default


def discover_agent_numbers(values: dict[str, str]) -> list[str]:
    numbers = set(DEFAULT_AGENTS)
    pattern = re.compile(r"^(?:AGENT|BOT)(\d+)_")
    for key in values:
        match = pattern.match(key)
        if match:
            numbers.add(match.group(1))
    return sorted(numbers, key=lambda item: int(item))


def profile_id(family: str, alias: str) -> str:
    return f"{safe_id(family or 'provider')}-{safe_id(alias or 'default')}"


def safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip()).strip("-._").lower() or "item"


def migrate(values: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    warnings: list[str] = []
    project_name = "zeroclaw-matrix-multi"
    matrix_profile = {
        "id": "matrix-default",
        "homeserver": values.get("MATRIX_HOMESERVER", ""),
        "allowed_rooms": list_value(values.get("MATRIX_ALLOWED_ROOMS")),
        "mention_only": bool_value(values.get("MATRIX_MENTION_ONLY"), False),
        "interrupt_on_new_message": bool_value(values.get("MATRIX_INTERRUPT_ON_NEW_MESSAGE"), True),
        "reply_in_thread": bool_value(values.get("MATRIX_REPLY_IN_THREAD"), True),
        "ack_reactions": bool_value(values.get("MATRIX_ACK_REACTIONS"), True),
        "stream_mode": values.get("MATRIX_STREAM_MODE", "off"),
        "multi_message": bool_value(values.get("MATRIX_MULTI_MESSAGE"), False),
        "multi_message_delay_ms": int_value(values.get("MATRIX_MULTI_MESSAGE_DELAY_MS"), 800),
        "channel_debounce_ms": int_value(values.get("CHANNEL_DEBOUNCE_MS"), 3000),
    }
    mcp_profile = {
        "id": "mcp-home",
        "enabled": bool_value(values.get("MCP_ENABLED"), False),
        "server_name": values.get("MCP_SERVER_NAME", "home"),
        "transport": values.get("MCP_TRANSPORT", "sse"),
        "url": values.get("MCP_URL", ""),
        "deferred_loading": bool_value(values.get("MCP_DEFERRED_LOADING"), True),
        "tool_timeout_secs": int_value(values.get("MCP_TOOL_TIMEOUT_SECS"), 120),
    }

    llm_profiles: dict[str, dict[str, Any]] = {}
    agents: list[dict[str, Any]] = []
    secrets_agents: dict[str, dict[str, str]] = {}

    for number in discover_agent_numbers(values):
        prefix = f"AGENT{number}_"
        legacy_prefix = f"BOT{number}_"
        name = f"agent{number}"
        family = first(values, f"{prefix}MODEL_PROVIDER_FAMILY", default="deepseek" if number == "1" else "ollama")
        alias = first(values, f"{prefix}MODEL_PROVIDER_ALIAS", default="text" if number == "1" else "local")
        profile = profile_id(family, alias)
        llm_profiles.setdefault(
            profile,
            {
                "id": profile,
                "provider_family": family,
                "provider_alias": alias,
                "model": first(values, f"{prefix}MODEL", f"DEEPSEEK_MODEL", default="deepseek-chat" if number == "1" else "qwen2.5:14b"),
                "base_url": first(
                    values,
                    f"{prefix}MODEL_BASE_URL",
                    "DEEPSEEK_BASE_URL",
                    default="https://api.deepseek.com/v1" if number == "1" else "http://host.docker.internal:11434",
                ),
                "wire_api": first(values, f"{prefix}MODEL_WIRE_API", "DEEPSEEK_WIRE_API", default="chat_completions"),
                "timeout_secs": int_value(values.get(f"{prefix}MODEL_TIMEOUT_SECS"), 120 if number != "2" else 600),
                "kind": values.get(f"{prefix}MODEL_KIND", ""),
            },
        )
        agent_matrix = {
            "user_id": first(values, f"{prefix}MATRIX_USER_ID", f"{legacy_prefix}MATRIX_USER_ID"),
            "device_id": first(values, f"{prefix}MATRIX_DEVICE_ID", f"{legacy_prefix}MATRIX_DEVICE_ID", default=f"ZEROCLAW_AGENT{number}"),
            "external_peers": list_value(first(values, f"{prefix}MATRIX_EXTERNAL_PEERS", f"{legacy_prefix}MATRIX_EXTERNAL_PEERS")),
            "peers": list_value(first(values, f"{prefix}MATRIX_PEERS", f"{legacy_prefix}MATRIX_PEERS")),
        }
        agent = {
            "id": name,
            "name": name,
            "enabled": True,
            "host_port": int_value(first(values, f"{prefix}HOST_PORT", f"{legacy_prefix}HOST_PORT"), 42640 + int(number)),
            "llm_profile": profile,
            "matrix_profile": "matrix-default",
            "mcp_profile": "mcp-home",
            "prompt_template": "default",
            "matrix": {key: value for key, value in agent_matrix.items() if value != "" and value != []},
        }
        agents.append(agent)
        secrets_agents[name] = {
            "model_api_key": first(values, f"{prefix}MODEL_API_KEY", "DEEPSEEK_API_KEY"),
            "matrix_access_token": first(values, f"{prefix}MATRIX_ACCESS_TOKEN", f"{legacy_prefix}MATRIX_ACCESS_TOKEN"),
            "matrix_password": first(values, f"{prefix}MATRIX_PASSWORD", f"{legacy_prefix}MATRIX_PASSWORD"),
            "matrix_recovery_key": first(values, f"{prefix}MATRIX_RECOVERY_KEY", f"{legacy_prefix}MATRIX_RECOVERY_KEY"),
            "mcp_gateway_token": first(values, f"{prefix}MCP_GATEWAY_TOKEN", "MCP_GATEWAY_TOKEN"),
        }
        if not agent["matrix"].get("external_peers") and not agent["matrix"].get("peers"):
            warnings.append(f"{name}: MATRIX_EXTERNAL_PEERS was empty; review Matrix peer access before starting.")

    manager = {
        "version": 1,
        "webui": {
            "default_language": values.get("WEBUI_DEFAULT_LANGUAGE", "en"),
            "default_theme": values.get("WEBUI_DEFAULT_THEME", "system"),
        },
        "server": {"bind_host": "127.0.0.1", "host_port": int_value(values.get("MANAGER_HOST_PORT"), 7652)},
        "docker": {
            "proxy_url": values.get("DOCKER_API_URL", "http://docker-socket-proxy:2375"),
            "project_name": project_name,
            "control_network": f"{project_name}_manager-control",
            "runtime_network": f"{project_name}_default",
            "matrix_host_ip": values.get("MATRIX_HOST_IP", "127.0.0.1"),
        },
        "paths": {
            "secrets_file": "/app/config/secrets.local.yaml",
            "generated_dir": "/app/config/generated",
            "instances_dir": "/app/instances",
        },
        "defaults": {
            "zeroclaw_image": values.get("ZEROCLAW_IMAGE", "ghcr.io/zeroclaw-labs/zeroclaw:v0.8.1-debian"),
            "matrix": matrix_profile_without_id(matrix_profile),
        },
        "vision": {
            "model": values.get("VISION_MODEL", "gpt-4o"),
            "base_url": values.get("VISION_BASE_URL", "https://api.openai.com/v1"),
            "wire_api": values.get("VISION_WIRE_API", "chat_completions"),
            "allow_remote_fetch": bool_value(values.get("VISION_ALLOW_REMOTE_FETCH"), False),
            "max_images": int_value(values.get("VISION_MAX_IMAGES"), 4),
            "max_image_size_mb": int_value(values.get("VISION_MAX_IMAGE_SIZE_MB"), 5),
            "max_image_turns": int_value(values.get("VISION_MAX_IMAGE_TURNS"), 2),
        },
        "heartbeat": {
            "enabled": bool_value(values.get("HEARTBEAT_ENABLED"), False),
            "interval_minutes": int_value(values.get("HEARTBEAT_INTERVAL_MINUTES"), 30),
            "two_phase": bool_value(values.get("HEARTBEAT_TWO_PHASE"), True),
            "message": values.get("HEARTBEAT_MESSAGE", ""),
            "adaptive": bool_value(values.get("HEARTBEAT_ADAPTIVE"), False),
            "min_interval_minutes": int_value(values.get("HEARTBEAT_MIN_INTERVAL_MINUTES"), 5),
            "max_interval_minutes": int_value(values.get("HEARTBEAT_MAX_INTERVAL_MINUTES"), 120),
            "deadman_timeout_minutes": int_value(values.get("HEARTBEAT_DEADMAN_TIMEOUT_MINUTES"), 0),
            "max_run_history": int_value(values.get("HEARTBEAT_MAX_RUN_HISTORY"), 100),
            "load_session_context": bool_value(values.get("HEARTBEAT_LOAD_SESSION_CONTEXT"), False),
            "task_timeout_secs": int_value(values.get("HEARTBEAT_TASK_TIMEOUT_SECS"), 600),
        },
        "pacing": {
            "loop_ignore_tools": list_value(values.get("PACING_LOOP_IGNORE_TOOLS")) or ["home__job_status"],
            "loop_detection_enabled": bool_value(values.get("PACING_LOOP_DETECTION_ENABLED"), True),
            "loop_detection_window_size": int_value(values.get("PACING_LOOP_DETECTION_WINDOW_SIZE"), 20),
            "loop_detection_max_repeats": int_value(values.get("PACING_LOOP_DETECTION_MAX_REPEATS"), 3),
        },
        "runtime": {
            "shell_timeout_secs": int_value(values.get("SHELL_TIMEOUT_SECS"), 300),
            "shell_tool_timeout_secs": int_value(values.get("SHELL_TOOL_TIMEOUT_SECS"), 300),
        },
        "profiles": {"llm": list(llm_profiles.values()), "matrix": [matrix_profile], "mcp": [mcp_profile]},
        "prompt_templates": [{"id": "default", "name": "Migrated default workspace", "files": {name: "" for name in ["AGENTS.md", "IDENTITY.md", "SOUL.md", "MEMORY.md", "TOOLS.md", "USER.md", "HEARTBEAT.md"]}}],
        "agents": agents,
    }
    secrets = {
        "version": 1,
        "vision": {"api_key": values.get("VISION_API_KEY", "")},
        "agents": secrets_agents,
        "proactive": {
            "enabled": bool_value(values.get("PROACTIVE_ENABLED"), False),
            "agents": values.get("PROACTIVE_AGENTS", values.get("PROACTIVE_BOTS", "")),
            "channels": values.get("PROACTIVE_CHANNELS", ""),
            "targets": values.get("PROACTIVE_TARGETS", ""),
            "poll_seconds": int_value(values.get("PROACTIVE_POLL_SECONDS"), 300),
            "random_min_minutes": int_value(values.get("PROACTIVE_RANDOM_MIN_MINUTES"), 90),
            "random_max_minutes": int_value(values.get("PROACTIVE_RANDOM_MAX_MINUTES"), 240),
            "cooldown_minutes": int_value(values.get("PROACTIVE_COOLDOWN_MINUTES"), 120),
            "quiet_hours": values.get("PROACTIVE_QUIET_HOURS", ""),
            "timezone": values.get("PROACTIVE_TIMEZONE", "Asia/Tokyo"),
            "prompt": values.get("PROACTIVE_PROMPT", ""),
        },
    }
    return manager, secrets, warnings


def matrix_profile_without_id(profile: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in profile.items() if key != "id"}


def write_yaml(path: Path, data: dict[str, Any], force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists; pass --force to overwrite migration output.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=False), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", default=".env", help="Path to legacy .env file.")
    parser.add_argument("--manager-out", default="config/manager.local.yaml", help="Output manager YAML path.")
    parser.add_argument("--secrets-out", default="config/secrets.local.yaml", help="Output secrets YAML path.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing migration output files.")
    args = parser.parse_args(argv)

    env_path = Path(args.env)
    if not env_path.exists():
        print(f"error: {env_path} does not exist", file=sys.stderr)
        return 2
    manager, secrets, warnings = migrate(parse_env(env_path))
    try:
        write_yaml(Path(args.manager_out), manager, args.force)
        write_yaml(Path(args.secrets_out), secrets, args.force)
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3
    print(f"wrote {args.manager_out}")
    print(f"wrote {args.secrets_out}")
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
