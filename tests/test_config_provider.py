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

    @mock.patch(
        "codex_session_relay.codex.keychain.read_secret",
        return_value="sk-" + "TEST_ONLY_secret_12345",
    )
    def test_runtime_keeps_key_out_of_command(self, _read):
        options, environment, model = codex.runtime(default_config(), "deepseek")
        fake_key = "sk-" + "TEST_ONLY_secret_12345"
        self.assertNotIn(fake_key, " ".join(options))
        self.assertEqual(environment["OPENAI_API_KEY"], fake_key)
        self.assertEqual(model, "deepseek-v4-flash")

    @mock.patch("codex_session_relay.codex.keychain.read_secret", return_value=None)
    def test_missing_key_fails_closed(self, _read):
        with self.assertRaises(RelayError):
            codex.runtime(default_config(), "deepseek")


if __name__ == "__main__":
    unittest.main()
