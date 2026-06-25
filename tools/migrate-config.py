#!/usr/bin/env python3
"""Split a legacy single-file manager.yaml into modular config files."""

from __future__ import annotations

import argparse
import copy
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


MODULES = {
    "llm": ("profiles", "llm", "llm"),
    "vision": ("profiles", "vision", "vision"),
    "matrix": ("profiles", "matrix", "matrix"),
    "mcp": ("profiles", "mcp", "mcp"),
    "agents": ("agents", None, "agents"),
    "skill_bundles": ("skill_bundles", None, "skills"),
}
ROOT_EXCLUDE = {"profiles", "agents", "prompt_templates", "skill_bundles"}
MOJIBAKE_MARKERS = ("\u9287", "\u935d", "\u93c0", "\u20ac", "\ufffd", "\u6d93", "\u7d31", "\u9428")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/manager.yaml", help="Legacy manager.yaml path.")
    parser.add_argument("--output-config", default="", help="New modular manager.yaml path. Defaults to --config.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing module files.")
    parser.add_argument("--no-backup", action="store_true", help="Do not create a timestamped backup of the legacy config.")
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    output_config = Path(args.output_config).resolve() if args.output_config else config_path
    project_root = config_path.parents[1] if config_path.parent.name == "config" else Path.cwd()
    legacy = read_yaml(config_path)
    if not isinstance(legacy, dict):
        raise SystemExit(f"{config_path} is not a YAML object")
    if isinstance(legacy.get("config_modules"), dict):
        raise SystemExit(f"{config_path} already uses modular config")

    modules = {
        "llm_dir": "config/llm",
        "vision_dir": "config/vision",
        "matrix_dir": "config/matrix",
        "mcp_dir": "config/mcp",
        "agents_dir": "config/agents",
        "prompts_dir": "config/prompts",
        "skills_dir": "config/skills",
        "secrets_file": "config/secrets.yaml",
    }
    root_payload = {key: copy.deepcopy(value) for key, value in legacy.items() if key not in ROOT_EXCLUDE}
    root_payload["version"] = 2
    root_payload["config_modules"] = modules

    written: list[Path] = []
    for _kind, (top_key, child_key, dir_name) in MODULES.items():
        values = legacy.get(top_key)
        if child_key:
            values = values.get(child_key) if isinstance(values, dict) else []
        if not isinstance(values, list):
            continue
        directory = project_root / "config" / dir_name
        for item in values:
            if not isinstance(item, dict):
                continue
            identifier = item_id(item)
            if not identifier:
                continue
            path = directory / f"{safe_file_stem(identifier)}.yaml"
            write_yaml(path, item, force=args.force)
            written.append(path)

    prompts = legacy.get("prompt_templates") if isinstance(legacy.get("prompt_templates"), list) else []
    for template in prompts:
        if not isinstance(template, dict):
            continue
        template_id = item_id(template)
        if not template_id:
            continue
        prompt_dir = project_root / "config" / "prompts" / ("example" if template_id == "default" else safe_file_stem(template_id))
        prompt_dir.mkdir(parents=True, exist_ok=True)
        files = template.get("files") if isinstance(template.get("files"), dict) else {}
        manifest_files: dict[str, str] = {}
        warnings: list[dict[str, Any]] = []
        for filename, content in files.items():
            name = str(filename)
            if not safe_prompt_filename(name):
                continue
            target = prompt_dir / name
            write_text(target, str(content), force=args.force)
            manifest_files[name] = name
            markers = [marker for marker in MOJIBAKE_MARKERS if marker in str(content)]
            if markers:
                warnings.append({"code": "possible_mojibake", "file": name, "markers": markers[:5]})
            written.append(target)
        manifest = {
            "id": str(template_id),
            "name": str(template.get("name") or template_id),
            "description": str(template.get("description") or ""),
            "encoding": "utf-8",
            "files": manifest_files,
        }
        if warnings:
            manifest["warnings"] = warnings
        manifest_path = prompt_dir / "manifest.yaml"
        write_yaml(manifest_path, manifest, force=args.force)
        written.append(manifest_path)

    if output_config == config_path and not args.no_backup:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = config_path.with_name(f"{config_path.stem}.legacy-{stamp}{config_path.suffix}")
        shutil.copy2(config_path, backup)
        print(f"backup: {backup}")

    write_yaml(output_config, root_payload, force=True)
    print(f"modular config: {output_config}")
    print(f"module files written: {len(written)}")


def read_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def write_yaml(path: Path, data: Any, force: bool) -> None:
    if path.exists() and not force:
        raise SystemExit(f"{path} already exists; use --force to overwrite")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def write_text(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        raise SystemExit(f"{path} already exists; use --force to overwrite")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def item_id(item: dict[str, Any]) -> str | None:
    for key in ("id", "alias", "server_name"):
        value = item.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def safe_file_stem(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value).strip()).strip("-._")
    return safe or "item"


def safe_prompt_filename(value: str) -> bool:
    return bool(value) and "/" not in value and "\\" not in value and ".." not in Path(value).parts


if __name__ == "__main__":
    main()
