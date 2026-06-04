from __future__ import annotations

import re


def normalize_spaces(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()
