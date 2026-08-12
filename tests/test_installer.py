from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InstallerTests(unittest.TestCase):
    def test_offline_install_creates_both_commands_and_verifies_versions(self):
        subprocess.run(
            ["python3", "scripts/build.py"], cwd=str(ROOT), check=True, capture_output=True
        )
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            install_dir = temp / "bin"
            env = dict(os.environ)
            env.update(
                {
                    "HOME": str(temp / "home"),
                    "CODEX_RELAY_INSTALL_DIR": str(install_dir),
                    "CODEX_RELAY_RELEASE_BASE": (ROOT / "dist").as_uri(),
                    "CODEX_RELAY_SKIP_PATH_UPDATE": "1",
                    "CODEX_RELAY_TEST_MODE": "1",
                }
            )
            result = subprocess.run(
                ["sh", "install.sh"],
                cwd=str(ROOT),
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((install_dir / "codex-relay").is_file())
            self.assertTrue((install_dir / "codex-model").is_symlink())
            for command in ("codex-relay", "codex-model"):
                version = subprocess.run(
                    [str(install_dir / command), "--version"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(version.stdout.strip(), "0.2.0")

    def test_insecure_release_source_is_rejected(self):
        env = dict(os.environ)
        env["CODEX_RELAY_RELEASE_BASE"] = "http://example.invalid/release"
        result = subprocess.run(
            ["sh", "install.sh"],
            cwd=str(ROOT),
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("HTTPS", result.stderr)

    def test_bad_checksum_does_not_replace_existing_command(self):
        subprocess.run(
            ["python3", "scripts/build.py"], cwd=str(ROOT), check=True, capture_output=True
        )
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            release = temp / "release"
            install_dir = temp / "bin"
            release.mkdir()
            install_dir.mkdir()
            shutil.copy2(ROOT / "dist" / "codex-relay-0.2.0.pyz", release)
            (release / "SHA256SUMS").write_text(
                "%s  codex-relay-0.2.0.pyz\n" % ("0" * 64), encoding="utf-8"
            )
            target = install_dir / "codex-relay"
            target.write_text("existing installation\n", encoding="utf-8")
            env = dict(os.environ)
            env.update(
                {
                    "CODEX_RELAY_INSTALL_DIR": str(install_dir),
                    "CODEX_RELAY_RELEASE_BASE": release.as_uri(),
                    "CODEX_RELAY_SKIP_PATH_UPDATE": "1",
                    "CODEX_RELAY_TEST_MODE": "1",
                }
            )
            result = subprocess.run(
                ["sh", "install.sh"],
                cwd=str(ROOT),
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("SHA-256", result.stderr)
            self.assertEqual(target.read_text(encoding="utf-8"), "existing installation\n")

    def test_existing_commands_are_backed_up_without_overwriting_older_backup(self):
        subprocess.run(
            ["python3", "scripts/build.py"], cwd=str(ROOT), check=True, capture_output=True
        )
        with tempfile.TemporaryDirectory() as temp_name:
            temp = Path(temp_name)
            install_dir = temp / "bin"
            install_dir.mkdir()
            relay = install_dir / "codex-relay"
            alias = install_dir / "codex-model"
            relay.write_text("old relay\n", encoding="utf-8")
            (install_dir / "codex-relay.previous").write_text(
                "older relay\n", encoding="utf-8"
            )
            alias.symlink_to("legacy-model")
            env = dict(os.environ)
            env.update(
                {
                    "CODEX_RELAY_INSTALL_DIR": str(install_dir),
                    "CODEX_RELAY_RELEASE_BASE": (ROOT / "dist").as_uri(),
                    "CODEX_RELAY_SKIP_PATH_UPDATE": "1",
                    "CODEX_RELAY_TEST_MODE": "1",
                }
            )
            result = subprocess.run(
                ["sh", "install.sh"], cwd=str(ROOT), env=env, capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                (install_dir / "codex-relay.previous.1").read_text(encoding="utf-8"),
                "old relay\n",
            )
            self.assertEqual(os.readlink(install_dir / "codex-model.previous"), "legacy-model")
            self.assertEqual(os.readlink(alias), "codex-relay")


if __name__ == "__main__":
    unittest.main()
