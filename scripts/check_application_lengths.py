#!/usr/bin/env python3
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT = (ROOT / "docs" / "open-source-application.md").read_text(encoding="utf-8")
FIELDS = re.findall(
    r"\*\*Recommended English \((\d+)/500 characters\)\*\*\n\n(.*?)(?=\n\n\*\*中文翻译\*\*)",
    TEXT,
    flags=re.DOTALL,
)
if len(FIELDS) != 3:
    raise SystemExit("expected 3 English fields, found %s" % len(FIELDS))
for recorded, field in FIELDS:
    actual = len(field.strip())
    if actual != int(recorded) or actual > 500:
        raise SystemExit("invalid field length: recorded=%s actual=%s" % (recorded, actual))
print("application fields: 3/3 within 500 characters")
