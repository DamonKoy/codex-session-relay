from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from codex_session_relay.util import sqlite_connection


class UtilTests(unittest.TestCase):
    def test_sqlite_connection_closes_after_context(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "state.sqlite"
            with sqlite_connection(path) as connection:
                connection.execute("CREATE TABLE example (id INTEGER PRIMARY KEY)")
            with self.assertRaises(sqlite3.ProgrammingError):
                connection.execute("SELECT 1")


if __name__ == "__main__":
    unittest.main()
