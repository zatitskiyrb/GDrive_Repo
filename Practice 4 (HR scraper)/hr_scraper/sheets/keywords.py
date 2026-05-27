from __future__ import annotations

from datetime import date

from models.schemas import Keyword
from sheets.client import SheetsClient


def read_active(client: SheetsClient) -> list[str]:
    rows = client.read_range("Keywords!A2:D")
    keywords = []
    for row in rows:
        if len(row) < 2:
            continue
        keyword, active = row[0], row[1]
        if active.strip().upper() == "TRUE":
            keywords.append(keyword.strip())
    return keywords


def seed(client: SheetsClient, keywords: list[str]) -> None:
    today = date.today().isoformat()
    rows = [[kw, "TRUE", today, ""] for kw in keywords]
    client.append_rows("Keywords!A2", rows)
