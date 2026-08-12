from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from codex_session_relay import model_cli
from codex_session_relay.config import default_config


class ModelCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.relay_home = self.root / "relay"
        self.codex_home = self.root / "codex"
        self.codex_home.mkdir()
        self.env = mock.patch.dict(
            os.environ,
            {
                "CODEX_HOME": str(self.codex_home),
                "CODEX_SESSION_RELAY_HOME": str(self.relay_home),
            },
            clear=False,
        )
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def invoke(self, argv):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = model_cli.main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    @mock.patch("codex_session_relay.model_cli.codex.run_provider", return_value=0)
    def test_gpt_launches_current_project_with_official_provider(self, run):
        with mock.patch("pathlib.Path.cwd", return_value=self.root):
            code, _, error = self.invoke(["gpt", "--", "--sandbox", "read-only"])
        self.assertEqual(code, 0)
        self.assertEqual(error, "")
        _, provider, model, passthrough, dry_run = run.call_args.args
        self.assertEqual(provider, "openai")
        self.assertIsNone(model)
        self.assertEqual(
            passthrough,
            ["-C", str(self.root.resolve()), "--sandbox", "read-only"],
        )
        self.assertFalse(dry_run)

    @mock.patch("codex_session_relay.model_cli.codex.run_provider", return_value=0)
    @mock.patch("codex_session_relay.model_cli.keychain.read_secret", return_value="TEST_KEY")
    def test_configured_deepseek_launches_without_prompt(self, _read, run):
        config = default_config()
        config["providers"]["deepseek"]["base_url"] = "https://gateway.example/v1/"
        config["providers"]["deepseek"].pop("setup_required")
        with mock.patch("codex_session_relay.model_cli.load_config", return_value=config):
            code, stdout, error = self.invoke(["deepseek", str(self.root)])
        self.assertEqual(code, 0)
        self.assertEqual(stdout, "")
        self.assertEqual(error, "")
        self.assertEqual(run.call_args.args[1], "deepseek")

    @mock.patch("codex_session_relay.model_cli.sys.stdin.isatty", return_value=False)
    def test_unconfigured_deepseek_fails_closed_without_tty(self, _isatty):
        code, _, error = self.invoke(["deepseek"])
        self.assertEqual(code, 1)
        self.assertIn("交互式终端", error)

    @mock.patch("codex_session_relay.model_cli.keychain.read_secret", return_value=None)
    def test_status_does_not_show_secret_and_checks_official_auth(self, _read):
        (self.codex_home / "auth.json").write_text("{}", encoding="utf-8")
        code, stdout, _ = self.invoke(["status"])
        report = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertTrue(report["gpt"]["ready"])
        self.assertEqual(report["deepseek"]["api_key"], "missing")

    def test_invalid_project_falls_back_to_current_directory(self):
        missing = self.root / "missing"
        with mock.patch("pathlib.Path.cwd", return_value=self.root):
            resolved = model_cli._resolve_project(str(missing))
        self.assertEqual(resolved, self.root.resolve())


if __name__ == "__main__":
    unittest.main()
