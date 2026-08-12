from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from codex_session_relay import codex
from codex_session_relay.config import (
    add_provider,
    configure_provider,
    default_config,
    load_config,
    save_config,
    validate_base_url,
)
from codex_session_relay.errors import RelayError


class ConfigProviderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.patch = mock.patch.dict(
            os.environ,
            {"CODEX_SESSION_RELAY_HOME": str(self.root / "relay")},
            clear=False,
        )
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.temp.cleanup()

    def test_config_is_created_with_0600_and_no_secret(self):
        config = load_config()
        path = self.root / "relay" / "config.json"
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("sk-", text.lower())
        self.assertNotIn("secret-value", text.lower())
        self.assertIn("deepseek", config["providers"])

    def test_legacy_pending_deepseek_profile_is_migrated_to_official_responses(self):
        relay = self.root / "relay"
        relay.mkdir(parents=True)
        path = relay / "config.json"
        legacy = default_config()
        legacy["providers"]["deepseek"].update(
            {
                "display_name": "DeepSeek",
                "base_url": None,
                "env_key": "OPENAI_API_KEY",
                "setup_required": "responses_gateway",
            }
        )
        legacy["providers"]["deepseek"].pop("model_catalog")
        path.write_text(json.dumps(legacy), encoding="utf-8")
        path.chmod(0o600)

        loaded = load_config()

        provider = loaded["providers"]["deepseek"]
        self.assertEqual(provider["base_url"], "https://api.deepseek.com/")
        self.assertEqual(provider["env_key"], "DEEPSEEK_API_KEY")
        self.assertEqual(provider["model_catalog"], "deepseek-v4")
        self.assertEqual(provider["minimum_codex_version"], "0.144.0")
        self.assertNotIn("setup_required", provider)

    def test_accepts_official_deepseek_responses_endpoint(self):
        self.assertEqual(
            validate_base_url("https://api.deepseek.com"),
            "https://api.deepseek.com/",
        )

    def test_rejects_insecure_remote_url(self):
        with self.assertRaises(RelayError):
            validate_base_url("http://example.com/v1")
        self.assertEqual(
            validate_base_url("http://127.0.0.1:8080/v1", True),
            "http://127.0.0.1:8080/v1/",
        )

    def test_add_provider_persists_only_keychain_reference(self):
        config = default_config()
        updated = add_provider(
            config,
            "example",
            "Example",
            "example-model",
            "https://models.example.test/v1",
            "EXAMPLE_API_KEY",
            False,
        )
        provider = updated["providers"]["example"]
        self.assertEqual(provider["keychain_service"], "codex-session-relay.provider.example")
        self.assertNotIn("secret", json.dumps(updated).lower())

    def test_builtin_deepseek_uses_official_responses_endpoint(self):
        config = default_config()
        provider = config["providers"]["deepseek"]
        self.assertEqual(provider["base_url"], "https://api.deepseek.com/")
        self.assertEqual(provider["env_key"], "DEEPSEEK_API_KEY")
        self.assertEqual(provider["model_catalog"], "deepseek-v4")
        self.assertEqual(provider["minimum_codex_version"], "0.144.0")

    def test_custom_deepseek_gateway_is_preserved(self):
        config = default_config()
        updated = configure_provider(
            config,
            "deepseek",
            "https://responses.example.test/v1",
            "",
            "",
            False,
        )
        self.assertEqual(
            updated["providers"]["deepseek"]["base_url"],
            "https://responses.example.test/v1/",
        )
        self.assertNotIn("model_catalog", updated["providers"]["deepseek"])

    @mock.patch(
        "codex_session_relay.codex.keychain.read_secret",
        return_value="sk-" + "TEST_ONLY_secret_12345",
    )
    def test_runtime_keeps_key_out_of_command(self, _read):
        config = default_config()
        options, environment, model = codex.runtime(config, "deepseek")
        fake_key = "sk-" + "TEST_ONLY_secret_12345"
        self.assertNotIn(fake_key, " ".join(options))
        self.assertEqual(environment["DEEPSEEK_API_KEY"], fake_key)
        self.assertIn("model_catalog_json=", " ".join(options))
        self.assertTrue((self.root / "relay" / "deepseek-v4-models.json").is_file())
        self.assertEqual(model, "deepseek-v4-flash")

    def test_openai_runtime_removes_external_provider_keys(self):
        with mock.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "TEST_OPENAI_OVERRIDE",
                "DEEPSEEK_API_KEY": "TEST_DEEPSEEK_OVERRIDE",
            },
            clear=False,
        ):
            _, environment, _ = codex.runtime(default_config(), "openai")
        self.assertNotIn("OPENAI_API_KEY", environment)
        self.assertNotIn("DEEPSEEK_API_KEY", environment)

    @mock.patch("codex_session_relay.codex.keychain.read_secret", return_value=None)
    def test_missing_key_fails_closed(self, _read):
        config = default_config()
        with self.assertRaises(RelayError):
            codex.runtime(config, "deepseek")

    @mock.patch("codex_session_relay.codex.version", return_value="0.143.2")
    def test_deepseek_rejects_unsupported_codex_version(self, _version):
        with self.assertRaisesRegex(RelayError, "0.144.0"):
            codex.require_minimum_version("0.144.0")

    @mock.patch("codex_session_relay.codex.version", return_value="0.147.0-alpha.1")
    def test_deepseek_accepts_newer_prerelease_codex_version(self, _version):
        codex.require_minimum_version("0.144.0")

if __name__ == "__main__":
    unittest.main()
