from __future__ import annotations

from models.schemas import Job
from sheets.client import SheetsClient


def existing_urls(client: SheetsClient) -> set[str]:
    rows = client.read_range("Jobs!F2:F")  # job_url column
    return {r[0] for r in rows if r}


def append_jobs(client: SheetsClient, jobs: list[Job]) -> None:
    if not jobs:
        return
    rows = [_to_row(j) for j in jobs]
    client.append_rows("Jobs!A2", rows)


def _to_row(j: Job) -> list:
    return [
        str(j.date_added),
        j.job_id,
        j.job_title,
        j.company_name,
        j.company_id,
        j.job_url,
        j.source,
        j.location,
        j.date_posted,
        j.employment_type,
        j.affinity_score,
        "; ".join(j.match_reasons),
        "; ".join(j.gap_reasons),
        j.job_description[:2000],  # ограничиваем длину для читаемости
    ]
