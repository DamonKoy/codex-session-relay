from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from codex_session_relay import cli
from tests.support import create_session, create_state_db, make_fake_codex


class CliExperienceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.codex_home = self.root / "codex"
        self.relay_home = self.root / "relay"
        self.session_id = "12345678-1234-1234-1234-123456789abc"
        self.session = self.codex_home / "sessions" / "source.jsonl"
        create_session(
            self.session,
            self.session_id,
            "custom",
            [
                json.dumps(
                    {
                        "type": "event_msg",
                        "payload": {"type": "user_message", "message": "hello"},
                    }
                )
            ],
        )
        create_state_db(
            self.codex_home / "state_5.sqlite",
            {
                "id": self.session_id,
                "model_provider": "custom",
                "model": "gpt-test",
                "title": "A long automation title\n" + "detail " * 30,
                "rollout_path": str(self.session),
                "cwd": str(self.root),
                "updated_at_ms": 1_700_000_000_000,
            },
        )
        (self.codex_home / "auth.json").write_text("{}", encoding="utf-8")
        binary = make_fake_codex(self.root)
        self.env = mock.patch.dict(
            os.environ,
            {
                "CODEX_HOME": str(self.codex_home),
                "CODEX_SESSION_RELAY_HOME": str(self.relay_home),
                "CODEX_CLI_PATH": str(binary),
                "CODEX_SESSION_RELAY_TEST_MODE": "1",
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
            code = cli.main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    @mock.patch("codex_session_relay.codex.keychain.read_secret", return_value=None)
    def test_doctor_human_output_treats_missing_key_as_setup_item(self, _read):
        code, stdout, stderr = self.invoke(["doctor"])
        self.assertEqual(code, 0)
        self.assertIn("[待配置] deepseek Responses 接口", stdout)
        self.assertIn("[待配置] deepseek API Key", stdout)
        self.assertIn("基础功能可用", stdout)
        self.assertEqual(stderr, "")

    @mock.patch("codex_session_relay.codex.keychain.read_secret", return_value=None)
    def test_doctor_json_remains_machine_readable(self, _read):
        code, stdout, _ = self.invoke(["doctor", "--json"])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(stdout)["ok"])

    def test_session_list_is_single_line_and_shows_id(self):
        code, stdout, _ = self.invoke(["session", "list", "--limit", "1"])
        self.assertEqual(code, 0)
        self.assertIn(self.session_id, stdout)
        self.assertIn("A long automation title detail", stdout)
        self.assertNotIn("automation title\ndetail", stdout)
        self.assertIn("…", stdout)

    def test_handoff_last_prints_review_command(self):
        package = self.root / "package"
        code, stdout, stderr = self.invoke(
            [
                "handoff",
                "prepare",
                "--last",
                "--project",
                str(self.root),
                "--to",
                "openai",
                "--output",
                str(package),
            ]
        )
        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertIn(str(package / "context.md"), stdout)
        self.assertIn("codex-relay handoff show", stdout)

    @mock.patch("codex_session_relay.codex.run_provider", return_value=0)
    def test_run_parses_relay_options_before_passthrough_boundary(self, run):
        code, _, _ = self.invoke(
            ["run", "openai", "--dry-run", "--", "-C", str(self.root)]
        )
        self.assertEqual(code, 0)
        _, provider, model, passthrough, dry_run = run.call_args.args
        self.assertEqual(provider, "openai")
        self.assertIsNone(model)
        self.assertEqual(passthrough, ["-C", str(self.root)])
        self.assertTrue(dry_run)


if __name__ == "__main__":
    unittest.main()
