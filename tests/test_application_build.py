from __future__ import annotations

import hashlib
import importlib.util
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from codex_session_relay import application
from codex_session_relay.errors import RelayError


ROOT = Path(__file__).resolve().parents[1]


class ApplicationBuildTests(unittest.TestCase):
    def test_application_uses_metrics_and_all_fields_fit(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "application.md"
            metrics = {
                "repo": "DamonKoy/codex-session-relay",
                "url": "https://github.com/DamonKoy/codex-session-relay",
                "description": "test",
                "stars": 0,
                "forks": 0,
                "contributors": 1,
                "license": "Apache-2.0",
                "default_branch": "main",
                "language": "Python",
                "open_issues": 0,
                "fetched_at": "2026-08-12T00:00:00+00:00",
            }
            with mock.patch("codex_session_relay.application.fetch_metrics", return_value=metrics):
                application.render("DamonKoy/codex-session-relay", "creator", output)
            text = output.read_text(encoding="utf-8")
            self.assertIn("0 stars, 0 forks, and 1 public contributor", text.lower())
            lengths = [int(value) for value in re.findall(r"\((\d+)/500 characters\)", text)]
            self.assertEqual(len(lengths), 3)
            self.assertTrue(all(value <= 500 for value in lengths))
            self.assertIn("**Role**: Primary maintainer", text)
            self.assertIn("Codex Security; API credits for my project", text)
            self.assertIn("Fill manually", text)
            self.assertIn("### Why the repository qualifies", text)
            self.assertIn("### How API credits will be used", text)
            self.assertIn("### Additional information", text)
            self.assertNotIn("[填写", text)

    def test_metric_copy_uses_singular_and_plural_labels(self):
        self.assertEqual(application._metric_count(0, "star"), "0 stars")
        self.assertEqual(application._metric_count(1, "star"), "1 star")
        self.assertEqual(application._metric_count(2, "public contributor"), "2 public contributors")

    def test_missing_repository_is_rejected(self):
        error = __import__("urllib.error").error.HTTPError(
            "https://api.github.com/repos/a/b", 404, "not found", {}, None
        )
        with mock.patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaises(RelayError):
                application.fetch_metrics("a/b")

    def test_reproducible_build(self):
        subprocess.run(["python3", "scripts/build.py"], cwd=str(ROOT), check=True, capture_output=True)
        first = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (ROOT / "dist").iterdir()
        }
        subprocess.run(["python3", "scripts/build.py"], cwd=str(ROOT), check=True, capture_output=True)
        second = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (ROOT / "dist").iterdir()
        }
        self.assertEqual(first, second)
        result = subprocess.run(
            ["python3", str(ROOT / "dist" / "codex-relay-0.3.0.pyz"), "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.stdout.strip(), "0.3.0")


if __name__ == "__main__":
    unittest.main()
