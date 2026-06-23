from __future__ import annotations

import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

import yaml

from tools.migrate_env_to_manager import main, migrate, parse_env


class MigrationToolTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_parse_env_handles_quotes_and_comments(self) -> None:
        env_path = self.root / ".env"
        env_path.write_text(
            """
# comment
MATRIX_HOMESERVER=https://matrix.example.com
AGENT1_MODEL="deepseek-chat"
AGENT1_MATRIX_PASSWORD='secret'
""",
            encoding="utf-8",
        )

        values = parse_env(env_path)

        self.assertEqual(values["AGENT1_MODEL"], "deepseek-chat")
        self.assertEqual(values["AGENT1_MATRIX_PASSWORD"], "secret")

    def test_migrate_preserves_agent_runtime_and_secrets(self) -> None:
        manager, secrets, warnings = migrate(
            {
                "ZEROCLAW_IMAGE": "example/zeroclaw:test",
                "MATRIX_HOMESERVER": "https://matrix.example.com",
                "MATRIX_ALLOWED_ROOMS": "!room:example.com",
                "AGENT1_HOST_PORT": "45678",
                "AGENT1_MODEL_PROVIDER_FAMILY": "openai",
                "AGENT1_MODEL_PROVIDER_ALIAS": "main",
                "AGENT1_MODEL": "gpt-test",
                "AGENT1_MODEL_BASE_URL": "https://api.example.com/v1",
                "AGENT1_MODEL_API_KEY": "model-secret",
                "AGENT1_MATRIX_USER_ID": "@agent1:example.com",
                "AGENT1_MATRIX_ACCESS_TOKEN": "matrix-token",
                "AGENT1_MATRIX_EXTERNAL_PEERS": "@you:example.com,#room:example.com",
                "AGENT1_MCP_GATEWAY_TOKEN": "mcp-token",
                "VISION_API_KEY": "vision-secret",
                "PROACTIVE_ENABLED": "true",
            }
        )

        self.assertIn("agent2", "\n".join(warnings))
        self.assertEqual(manager["defaults"]["zeroclaw_image"], "example/zeroclaw:test")
        self.assertEqual(manager["agents"][0]["host_port"], 45678)
        self.assertEqual(manager["profiles"]["llm"][0]["provider_family"], "openai")
        self.assertEqual(manager["profiles"]["llm"][0]["model"], "gpt-test")
        self.assertEqual(manager["agents"][0]["matrix"]["external_peers"], ["@you:example.com", "#room:example.com"])
        self.assertEqual(secrets["vision"]["api_key"], "vision-secret")
        self.assertEqual(secrets["agents"]["agent1"]["model_api_key"], "model-secret")
        self.assertEqual(secrets["agents"]["agent1"]["matrix_access_token"], "matrix-token")
        self.assertEqual(secrets["agents"]["agent1"]["mcp_gateway_token"], "mcp-token")
        self.assertTrue(secrets["proactive"]["enabled"])

    def test_cli_refuses_to_overwrite_outputs(self) -> None:
        env_path = self.root / ".env"
        manager_out = self.root / "manager.local.yaml"
        secrets_out = self.root / "secrets.local.yaml"
        env_path.write_text("MATRIX_HOMESERVER=https://matrix.example.com\n", encoding="utf-8")
        manager_out.write_text("existing: true\n", encoding="utf-8")

        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            code = main(["--env", str(env_path), "--manager-out", str(manager_out), "--secrets-out", str(secrets_out)])

        self.assertEqual(code, 3)
        self.assertEqual(yaml.safe_load(manager_out.read_text(encoding="utf-8")), {"existing": True})

    def test_cli_writes_yaml_outputs_with_force(self) -> None:
        env_path = self.root / ".env"
        manager_out = self.root / "manager.local.yaml"
        secrets_out = self.root / "secrets.local.yaml"
        env_path.write_text("MATRIX_HOMESERVER=https://matrix.example.com\n", encoding="utf-8")

        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            code = main(["--env", str(env_path), "--manager-out", str(manager_out), "--secrets-out", str(secrets_out), "--force"])

        self.assertEqual(code, 0)
        self.assertEqual(yaml.safe_load(manager_out.read_text(encoding="utf-8"))["version"], 1)
        self.assertEqual(yaml.safe_load(secrets_out.read_text(encoding="utf-8"))["version"], 1)


if __name__ == "__main__":
    unittest.main()
