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

    def test_legacy_direct_deepseek_endpoint_is_migrated_to_pending_setup(self):
        relay = self.root / "relay"
        relay.mkdir(parents=True)
        path = relay / "config.json"
        legacy = default_config()
        legacy["providers"]["deepseek"]["base_url"] = "https://api.deepseek.com/"
        legacy["providers"]["deepseek"].pop("setup_required")
        path.write_text(json.dumps(legacy), encoding="utf-8")
        path.chmod(0o600)

        loaded = load_config()

        self.assertIsNone(loaded["providers"]["deepseek"]["base_url"])
        self.assertEqual(
            loaded["providers"]["deepseek"]["setup_required"],
            "responses_gateway",
        )

    def test_rejects_official_deepseek_chat_endpoint_as_responses(self):
        with self.assertRaises(RelayError):
            validate_base_url("https://api.deepseek.com")

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

    def test_builtin_deepseek_requires_explicit_responses_endpoint(self):
        config = default_config()
        self.assertIsNone(config["providers"]["deepseek"]["base_url"])
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
        self.assertNotIn("setup_required", updated["providers"]["deepseek"])

    @mock.patch(
        "codex_session_relay.codex.keychain.read_secret",
        return_value="sk-" + "TEST_ONLY_secret_12345",
    )
    def test_runtime_keeps_key_out_of_command(self, _read):
        config = default_config()
        config["providers"]["deepseek"]["base_url"] = "https://responses.example.test/v1/"
        config["providers"]["deepseek"].pop("setup_required")
        options, environment, model = codex.runtime(config, "deepseek")
        fake_key = "sk-" + "TEST_ONLY_secret_12345"
        self.assertNotIn(fake_key, " ".join(options))
        self.assertEqual(environment["OPENAI_API_KEY"], fake_key)
        self.assertEqual(model, "deepseek-v4-flash")

    @mock.patch("codex_session_relay.codex.keychain.read_secret", return_value=None)
    def test_missing_key_fails_closed(self, _read):
        config = default_config()
        config["providers"]["deepseek"]["base_url"] = "https://responses.example.test/v1/"
        config["providers"]["deepseek"].pop("setup_required")
        with self.assertRaises(RelayError):
            codex.runtime(config, "deepseek")

    def test_unconfigured_deepseek_fails_before_keychain_access(self):
        with mock.patch("codex_session_relay.codex.keychain.read_secret") as read:
            with self.assertRaises(RelayError):
                codex.runtime(default_config(), "deepseek")
            read.assert_not_called()


if __name__ == "__main__":
    unittest.main()
