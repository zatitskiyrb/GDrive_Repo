from __future__ import annotations

import time

import httpx

from models.schemas import Job
from scrapers.base import BaseScraper

_API_URL = "https://remoteok.com/api"
_HEADERS = {"User-Agent": "hr-scraper/1.0"}


class RemoteOKScraper(BaseScraper):
    SOURCE = "RemoteOK"

    def search(self, keywords: list[str], location: str, days: int) -> list[Job]:
        try:
            all_jobs = self._fetch_all()
        except Exception as exc:
            print(f"[RemoteOK] Fetch failed: {exc}")
            return []

        jobs: list[Job] = []
        seen: set[str] = set()
        keywords_lower = [k.lower() for k in keywords]

        for item in all_jobs:
            if not isinstance(item, dict):
                continue
            tags = item.get("tags") or []
            text = " ".join([
                item.get("position", ""),
                " ".join(tags) if isinstance(tags, list) else str(tags),
                item.get("description", ""),
            ]).lower()
            if not any(kw in text for kw in keywords_lower):
                continue

            job_url = item.get("url", "")
            if not job_url or job_url in seen:
                continue
            seen.add(job_url)

            jobs.append(Job.create(
                job_url=job_url,
                job_title=item.get("position", "").strip(),
                company_name=item.get("company", "").strip(),
                source=self.SOURCE,
                location="Remote",
                date_posted=item.get("date", "").strip(),
                job_description=item.get("description", "").strip(),
            ))

        return jobs

    def _fetch_all(self) -> list[dict]:
        resp = httpx.get(_API_URL, headers=_HEADERS, timeout=20, follow_redirects=True)
        resp.raise_for_status()
        data = resp.json()
        # First item is metadata, rest are jobs
        return data[1:] if isinstance(data, list) and data else []
