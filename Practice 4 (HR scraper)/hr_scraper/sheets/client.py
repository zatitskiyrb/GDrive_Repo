from __future__ import annotations

import os
from functools import cached_property
from pathlib import Path

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

JOBS_HEADERS = [
    "date_added", "job_id", "job_title", "company_name", "company_id",
    "job_url", "source", "location", "date_posted", "employment_type",
    "affinity_score", "match_reasons", "gap_reasons", "job_description",
]

COMPANIES_HEADERS = [
    "company_id", "company_name", "company_website",
    "source", "date_added", "total_jobs", "notes",
]

KEYWORDS_HEADERS = ["keyword", "active", "date_added", "notes"]


class SheetsClient:
    def __init__(self, sheet_id: str | None = None):
        self._sheet_id = sheet_id or os.getenv("GOOGLE_SHEET_ID", "")
        creds_path = Path(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "credentials/service_account.json"))
        creds = Credentials.from_service_account_file(str(creds_path), scopes=_SCOPES)
        self._service = build("sheets", "v4", credentials=creds, cache_discovery=False)

    @cached_property
    def _sheets(self):
        return self._service.spreadsheets()

    # ------------------------------------------------------------------
    # Spreadsheet lifecycle
    # ------------------------------------------------------------------

    @property
    def sheet_id(self) -> str:
        return self._sheet_id

    def ensure_tabs(self) -> None:
        """Create any missing tabs (Jobs, Companies, Keywords) in the existing spreadsheet."""
        meta = self._sheets.get(spreadsheetId=self._sheet_id).execute()
        existing = {s["properties"]["title"] for s in meta.get("sheets", [])}

        required = {
            "Jobs": JOBS_HEADERS,
            "Companies": COMPANIES_HEADERS,
            "Keywords": KEYWORDS_HEADERS,
        }
        add_requests = [
            {"addSheet": {"properties": {"title": tab}}}
            for tab in required
            if tab not in existing
        ]
        if add_requests:
            self._sheets.batchUpdate(
                spreadsheetId=self._sheet_id,
                body={"requests": add_requests},
            ).execute()

        # Write headers for newly created tabs
        header_updates = [
            (f"{tab}!A1", [headers])
            for tab, headers in required.items()
            if tab not in existing
        ]
        if header_updates:
            self.batch_update_values(header_updates)

    # ------------------------------------------------------------------
    # Read / write primitives
    # ------------------------------------------------------------------

    def read_range(self, range_: str) -> list[list]:
        resp = self._sheets.values().get(
            spreadsheetId=self._sheet_id, range=range_
        ).execute()
        return resp.get("values", [])

    def append_rows(self, range_: str, rows: list[list]) -> None:
        if not rows:
            return
        self._sheets.values().append(
            spreadsheetId=self._sheet_id,
            range=range_,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": rows},
        ).execute()

    def batch_update_values(self, updates: list[tuple[str, list[list]]]) -> None:
        data = [{"range": r, "values": v} for r, v in updates]
        self._sheets.values().batchUpdate(
            spreadsheetId=self._sheet_id,
            body={"valueInputOption": "USER_ENTERED", "data": data},
        ).execute()
