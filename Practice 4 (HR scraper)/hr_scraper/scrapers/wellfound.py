from __future__ import annotations

import time
import urllib.parse

from models.schemas import Job
from scrapers.base import BaseScraper


class WellfoundScraper(BaseScraper):
    SOURCE = "Wellfound"

    def search(self, keywords: list[str], location: str, days: int) -> list[Job]:
        jobs: list[Job] = []
        seen: set[str] = set()

        for keyword in keywords:
            try:
                raw_jobs = self._search_keyword(keyword, location)
                for job in raw_jobs:
                    if job.job_url not in seen:
                        seen.add(job.job_url)
                        jobs.append(job)
                time.sleep(2.0)
            except Exception as exc:
                print(f"[Wellfound] Error searching '{keyword}': {exc}")

        return jobs

    def _search_keyword(self, keyword: str, location: str) -> list[Job]:
        from playwright.sync_api import sync_playwright

        params = {"role": keyword}
        if location.lower() == "remote":
            params["remote"] = "true"
        else:
            params["location_roles"] = location

        url = "https://wellfound.com/jobs?" + urllib.parse.urlencode(params)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(3000)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)
            html = page.content()
            browser.close()

        return self._parse_html(html)

    def _parse_html(self, html: str) -> list[Job]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        jobs: list[Job] = []

        for card in soup.select("div[class*='JobListing'], div[data-test='JobListing']"):
            try:
                title_el = card.select_one("a[class*='jobTitle'], h2 a, h3 a")
                company_el = card.select_one("a[class*='companyName'], span[class*='company']")
                location_el = card.select_one("span[class*='location']")

                if not title_el:
                    continue

                href = title_el.get("href", "")
                job_url = f"https://wellfound.com{href}" if href.startswith("/") else href
                if not job_url:
                    continue

                jobs.append(Job.create(
                    job_url=job_url,
                    job_title=title_el.get_text(strip=True),
                    company_name=company_el.get_text(strip=True) if company_el else "",
                    source=self.SOURCE,
                    location=location_el.get_text(strip=True) if location_el else "",
                ))
            except Exception:
                continue

        return jobs
