from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from codex_session_relay import history
from codex_session_relay.errors import RelayError
from tests.support import create_session, create_state_db, make_fake_codex


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.codex_home = self.root / "codex"
        self.relay_home = self.root / "relay"
        self.binary = make_fake_codex(self.root)
        self.session_id = "11111111-2222-3333-4444-555555555555"
        self.session = self.codex_home / "sessions" / "source.jsonl"
        self.original = create_session(
            self.session,
            self.session_id,
            "deepseek",
            [json.dumps({"type": "event_msg", "payload": {"type": "agent_message", "message": "done"}})],
        )
        create_state_db(
            self.codex_home / "state_5.sqlite",
            {
                "id": self.session_id,
                "model_provider": "deepseek",
                "model": "deepseek-v4-flash",
                "title": "Task",
                "rollout_path": str(self.session),
                "cwd": str(self.root),
            },
        )
        self.env = mock.patch.dict(
            os.environ,
            {
                "CODEX_HOME": str(self.codex_home),
                "CODEX_SESSION_RELAY_HOME": str(self.relay_home),
                "CODEX_CLI_PATH": str(self.binary),
                "CODEX_SESSION_RELAY_TEST_MODE": "1",
            },
            clear=False,
        )
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_audit_plan_apply_and_rollback_preserve_tail(self):
        audit = history.audit()
        self.assertEqual(audit["normalization_candidates"], 1)
        plan_path = self.root / "plan.json"
        plan = history.create_normalize_plan(plan_path)
        original_tail = self.original.partition(b"\n")[2]
        result = history.apply_normalize(plan_path, plan["confirmation_sha256"])
        migrated = self.session.read_bytes()
        self.assertIn(b'"model_provider": "custom"', migrated.partition(b"\n")[0])
        self.assertEqual(migrated.partition(b"\n")[2], original_tail)
        with sqlite3.connect(str(self.codex_home / "state_5.sqlite")) as connection:
            self.assertEqual(connection.execute("SELECT model_provider FROM threads").fetchone()[0], "custom")
        backup = Path(result["backup"])
        manifest = json.loads((backup / "manifest.json").read_text(encoding="utf-8"))
        history.rollback(backup, manifest["confirmation_sha256"])
        self.assertEqual(self.session.read_bytes(), self.original)
        with sqlite3.connect(str(self.codex_home / "state_5.sqlite")) as connection:
            self.assertEqual(connection.execute("SELECT model_provider FROM threads").fetchone()[0], "deepseek")

    def test_changed_session_rejects_and_restores(self):
        plan_path = self.root / "plan.json"
        plan = history.create_normalize_plan(plan_path)
        self.session.write_bytes(self.session.read_bytes() + b'{"type":"event_msg"}\n')
        with self.assertRaises(RelayError):
            history.apply_normalize(plan_path, plan["confirmation_sha256"])
        self.assertIn(b'"model_provider": "deepseek"', self.session.read_bytes().partition(b"\n")[0])

    def test_bad_confirmation_and_lock_fail_closed(self):
        plan_path = self.root / "plan.json"
        history.create_normalize_plan(plan_path)
        with self.assertRaises(RelayError):
            history.apply_normalize(plan_path, "bad")
        self.relay_home.mkdir(parents=True, exist_ok=True)
        (self.relay_home / "history.lock").write_text("locked", encoding="utf-8")
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        with self.assertRaises(RelayError):
            history.apply_normalize(plan_path, plan["confirmation_sha256"])

    def test_tagging_is_idempotent_and_confirmed(self):
        plan_path = self.root / "tag.json"
        plan = history.create_tag_plan(plan_path)
        self.assertEqual(plan["items"][0]["new_title"], "[DS] Task")
        history.apply_tag_plan(plan_path, plan["confirmation_sha256"])
        second = history.create_tag_plan(self.root / "tag2.json")
        self.assertEqual(second["items"], [])

    def test_corrupt_backup_is_rejected(self):
        plan_path = self.root / "plan.json"
        plan = history.create_normalize_plan(plan_path)
        result = history.apply_normalize(plan_path, plan["confirmation_sha256"])
        backup = Path(result["backup"])
        manifest = json.loads((backup / "manifest.json").read_text(encoding="utf-8"))
        (backup / "state_5.sqlite").write_bytes(b"corrupt")
        with self.assertRaises(RelayError):
            history.rollback(backup, manifest["confirmation_sha256"])

    def test_active_client_is_rejected(self):
        plan_path = self.root / "plan.json"
        plan = history.create_normalize_plan(plan_path)
        with mock.patch("codex_session_relay.history.codex.active_clients", return_value=["Codex"]):
            with self.assertRaises(RelayError):
                history.apply_normalize(plan_path, plan["confirmation_sha256"])

    def test_unknown_schema_is_rejected(self):
        with sqlite3.connect(str(self.codex_home / "state_5.sqlite")) as connection:
            connection.execute("ALTER TABLE threads RENAME TO old_threads")
            connection.execute("CREATE TABLE threads (id TEXT PRIMARY KEY)")
        with self.assertRaises(RelayError):
            history.audit()


if __name__ == "__main__":
    unittest.main()
