from __future__ import annotations

import subprocess
import unittest
from unittest import mock

from codex_session_relay import keychain
from codex_session_relay.errors import RelayError


class KeychainTests(unittest.TestCase):
    def test_store_command_contains_no_secret_argument(self):
        command = keychain._store_command("relay.test", "tester")
        self.assertEqual(command[-1], "-w")
        self.assertNotIn("TEST_ONLY_secret", command)

    @mock.patch("codex_session_relay.keychain.sys.platform", "darwin")
    @mock.patch("codex_session_relay.keychain._security_find")
    def test_missing_item_is_normal_first_run_state(self, find):
        find.return_value = (44, "", "item could not be found")
        self.assertIsNone(keychain.read_secret("relay.test", "tester"))

    @mock.patch("codex_session_relay.keychain.sys.platform", "darwin")
    @mock.patch("codex_session_relay.keychain._security_find")
    def test_read_returns_secret_without_logging_it(self, find):
        find.return_value = (0, "TEST_ONLY_secret", "")
        self.assertEqual(
            keychain.read_secret("relay.test", "tester"), "TEST_ONLY_secret"
        )

    @mock.patch("codex_session_relay.keychain.sys.platform", "darwin")
    @mock.patch("codex_session_relay.keychain.read_secret")
    @mock.patch("codex_session_relay.keychain._security_store")
    def test_new_secret_uses_no_argv_store_and_verifies(self, store, read):
        store.return_value = 0
        read.return_value = "TEST_ONLY_secret"

        keychain.write_secret("relay.test", "TEST_ONLY_secret", "tester")

        store.assert_called_once_with("relay.test", "tester", "TEST_ONLY_secret")
        read.assert_called_once_with("relay.test", "tester")

    @mock.patch("codex_session_relay.keychain.sys.platform", "darwin")
    @mock.patch("codex_session_relay.keychain._security_find")
    def test_unexpected_security_error_fails_closed(self, find):
        find.return_value = (1, "", "authorization denied")
        with self.assertRaises(RelayError):
            keychain.read_secret("relay.test", "tester")

    @mock.patch("codex_session_relay.keychain.sys.platform", "darwin")
    @mock.patch("codex_session_relay.keychain.subprocess.run")
    @mock.patch("codex_session_relay.keychain._security_find")
    def test_delete_uses_only_service_and_account(self, find, run):
        find.return_value = (0, "TEST_ONLY_secret", "")
        run.return_value = subprocess.CompletedProcess([], 0, "", "")
        self.assertTrue(keychain.delete_secret("relay.test", "tester"))
        command = run.call_args.args[0]
        self.assertNotIn("TEST_ONLY_secret", command)
        self.assertEqual(command[-1], "relay.test")


if __name__ == "__main__":
    unittest.main()
