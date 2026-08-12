#!/usr/bin/env python3
from __future__ import annotations

import gzip
import hashlib
import io
import os
import shutil
import tarfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
VERSION = "0.3.0"
FIXED_ZIP_TIME = (2020, 1, 1, 0, 0, 0)
SOURCE_FILES = [
    path
    for path in sorted(ROOT.rglob("*"))
    if path.is_file()
    and not (
        {".git", "dist", "build", "__pycache__", ".pytest_cache", ".venv"}
        & set(path.parts)
    )
    and not any(part.endswith(".egg-info") for part in path.parts)
    and path.name not in {".coverage", ".DS_Store", "open-source-application-final.md"}
    and not path.name.endswith((".pyc", ".pyo"))
]


def zip_info(name: str, executable: bool = False) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = ((0o755 if executable else 0o644) & 0xFFFF) << 16
    return info


def build_pyz(target: Path) -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        entry = "from codex_session_relay.entrypoint import main\nraise SystemExit(main())\n"
        archive.writestr(zip_info("__main__.py"), entry.encode("utf-8"))
        source_root = ROOT / "src"
        for path in sorted((source_root / "codex_session_relay").rglob("*.py")):
            archive.writestr(
                zip_info(str(path.relative_to(source_root))), path.read_bytes()
            )
    target.write_bytes(b"#!/usr/bin/env python3\n" + buffer.getvalue())
    os.chmod(str(target), 0o755)


def build_source_archive(target: Path) -> None:
    raw_tar = io.BytesIO()
    prefix = "codex-session-relay-%s" % VERSION
    with tarfile.open(fileobj=raw_tar, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for path in SOURCE_FILES:
            relative = path.relative_to(ROOT)
            data = path.read_bytes()
            info = tarfile.TarInfo("%s/%s" % (prefix, relative))
            info.size = len(data)
            info.mode = 0o755 if os.access(str(path), os.X_OK) else 0o644
            info.mtime = 0
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            archive.addfile(info, io.BytesIO(data))
    with target.open("wb") as handle:
        with gzip.GzipFile(filename="", mode="wb", fileobj=handle, mtime=0, compresslevel=9) as compressed:
            compressed.write(raw_tar.getvalue())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if DIST.exists():
        shutil.rmtree(str(DIST))
    DIST.mkdir()
    pyz = DIST / ("codex-relay-%s.pyz" % VERSION)
    source = DIST / ("codex-session-relay-%s.tar.gz" % VERSION)
    build_pyz(pyz)
    build_source_archive(source)
    checksum = DIST / "SHA256SUMS"
    checksum.write_text(
        "\n".join("%s  %s" % (sha256(path), path.name) for path in (pyz, source)) + "\n",
        encoding="utf-8",
    )
    print(checksum.read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
