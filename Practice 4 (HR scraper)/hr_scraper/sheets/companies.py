from __future__ import annotations

from models.schemas import Company
from sheets.client import SheetsClient
from utils.normalizer import normalize_company


def _load_index(client: SheetsClient) -> dict[str, Company]:
    rows = client.read_range("Companies!A2:G")
    index: dict[str, Company] = {}
    for row in rows:
        if not row:
            continue
        row += [""] * (7 - len(row))
        c = Company(
            company_id=row[0],
            company_name=row[1],
            company_website=row[2],
            source=row[3],
            date_added=row[4] or str(__import__("datetime").date.today()),
            total_jobs=int(row[5]) if row[5] else 1,
            notes=row[6],
        )
        index[normalize_company(c.company_name)] = c
    return index


def find_or_create(client: SheetsClient, name: str, website: str, source: str) -> Company:
    index = _load_index(client)
    key = normalize_company(name)

    if key in index:
        return index[key]

    company = Company.create(name=name, website=website, source=source)
    client.append_rows("Companies!A2", [_to_row(company)])
    return company


def update_job_counts(client: SheetsClient) -> None:
    rows = client.read_range("Companies!A2:G")
    if not rows:
        return

    # Read all jobs and count per company_id
    job_rows = client.read_range("Jobs!E2:E")  # company_id column
    counts: dict[str, int] = {}
    for r in job_rows:
        if r:
            cid = r[0]
            counts[cid] = counts.get(cid, 0) + 1

    updates = []
    for i, row in enumerate(rows, start=2):
        if not row:
            continue
        cid = row[0]
        count = counts.get(cid, 0)
        updates.append((f"Companies!F{i}", [[count]]))

    if updates:
        client.batch_update_values(updates)


def _to_row(c: Company) -> list:
    return [
        c.company_id,
        c.company_name,
        c.company_website,
        c.source,
        str(c.date_added),
        c.total_jobs,
        c.notes,
    ]
