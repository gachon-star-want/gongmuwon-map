from __future__ import annotations

import re
from datetime import date

_DATE_RE = re.compile(r"(20\d{2})[./-](\d{1,2})[./-](\d{1,2})")
_KOREAN_DATE_RE = re.compile(r"(20\d{2})년\s*(\d{1,2})월\s*(\d{1,2})일")


def parse_crawler_date(raw: str) -> date | None:
    value = raw.strip()
    match = _DATE_RE.search(value)
    if match:
        year, month, day = (int(part) for part in match.groups())
        return date(year, month, day)
    match = _KOREAN_DATE_RE.search(value)
    if match:
        year, month, day = (int(part) for part in match.groups())
        return date(year, month, day)
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
