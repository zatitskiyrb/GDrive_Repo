from __future__ import annotations

import time

import httpx

from models.schemas import Job
from scrapers.base import BaseScraper


class GreenhouseScraper(BaseScraper):
    SOURCE = "Greenhouse"

    def __init__(self, company_boards: list[str]):
        self._boards = company_boards

    def search(self, keywords: list[str], location: str, days: int, limit: int = 100) -> list[Job]:
        jobs: list[Job] = []
        kw_lower = [kw.lower() for kw in keywords]

        for board in self._boards:
            if len(jobs) >= limit:
                break
            try:
                board_jobs = self._fetch_board(board)
                for raw in board_jobs:
                    if len(jobs) >= limit:
                        break
                    if self._matches(raw, kw_lower, location):
                        job = self._parse(raw, board)
                        if job:
                            jobs.append(job)
                time.sleep(0.3)
            except Exception as exc:
                print(f"[Greenhouse] Error fetching {board}: {exc}")

        return jobs

    def _fetch_board(self, board: str) -> list[dict]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
        resp = httpx.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json().get("jobs", [])

    def _matches(self, raw: dict, kw_lower: list[str], location: str) -> bool:
        title = raw.get("title", "").lower()
        loc = raw.get("location", {}).get("name", "").lower()
        title_match = any(kw in title for kw in kw_lower)
        loc_match = (
            not location
            or location.lower() == "remote"
            or location.lower() in loc
            or "remote" in loc
        )
        return title_match and loc_match

    def _parse(self, raw: dict, board: str) -> Job | None:
        url = raw.get("absolute_url", "")
        if not url:
            return None

        return Job.create(
            job_url=url,
            job_title=raw.get("title", ""),
            company_name=board.replace("-", " ").title(),
            source=self.SOURCE,
            location=raw.get("location", {}).get("name", ""),
            date_posted=raw.get("updated_at", "")[:10],
            job_description=raw.get("content", "")[:3000],
        )
