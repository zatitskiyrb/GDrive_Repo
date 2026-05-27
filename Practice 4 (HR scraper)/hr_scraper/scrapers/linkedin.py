from __future__ import annotations

import time

from models.schemas import Job
from scrapers.base import BaseScraper


class LinkedInScraper(BaseScraper):
    SOURCE = "LinkedIn"

    def search(self, keywords: list[str], location: str, days: int, limit: int = 100) -> list[Job]:
        from jobspy import scrape_jobs

        jobs: list[Job] = []
        seen: set[str] = set()

        for keyword in keywords:
            if len(jobs) >= limit:
                break
            remaining = limit - len(jobs)
            try:
                df = scrape_jobs(
                    site_name=["linkedin"],
                    search_term=keyword,
                    location=location,
                    results_wanted=min(remaining, 5),
                    hours_old=days * 24,
                    verbose=0,
                )
                if df is not None and not df.empty:
                    for _, row in df.iterrows():
                        if len(jobs) >= limit:
                            break
                        try:
                            job_url = str(row.get("job_url") or "").strip()
                            if not job_url or job_url in seen:
                                continue
                            seen.add(job_url)
                            jobs.append(Job.create(
                                job_url=job_url,
                                job_title=str(row.get("title") or "").strip(),
                                company_name=str(row.get("company") or "").strip(),
                                source=self.SOURCE,
                                location=str(row.get("location") or "").strip(),
                                date_posted=str(row.get("date_posted") or "").strip(),
                                job_description=str(row.get("description") or "").strip(),
                            ))
                        except Exception:
                            continue
                time.sleep(2.0)
            except Exception as exc:
                print(f"[LinkedIn] Error searching '{keyword}': {exc}")

        return jobs
