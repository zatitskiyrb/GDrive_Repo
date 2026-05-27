from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Ensure project root is on path so submodules import cleanly
sys.path.insert(0, str(Path(__file__).parent))

load_dotenv(override=True)


def run() -> None:
    config = _load_config()

    # ------------------------------------------------------------------
    # 1. Setup
    # ------------------------------------------------------------------
    from utils.cv_parser import parse_cv
    from utils.dedup import filter_new, load, save

    cv_text = parse_cv(config["cv"]["path"])
    processed_urls = load()

    # ------------------------------------------------------------------
    # 2. Google Sheets — init or connect
    # ------------------------------------------------------------------
    from sheets.client import SheetsClient
    import sheets.keywords as kw_sheet
    import sheets.jobs as jobs_sheet
    import sheets.companies as companies_sheet

    sheet_id = os.getenv("GOOGLE_SHEET_ID", "")
    if not sheet_id:
        raise SystemExit(
            "[Error] GOOGLE_SHEET_ID is not set in .env.\n"
            "Create a Google Sheet, share it with the Service Account as Editor, "
            "then set GOOGLE_SHEET_ID=<id> in .env."
        )
    client = SheetsClient(sheet_id)

    # Create missing tabs (Jobs, Companies, Keywords) if they don't exist yet
    client.ensure_tabs()
    print(f"[Sheets] Connected to spreadsheet: {sheet_id}")

    # Seed Keywords tab if it's empty
    existing_kws = kw_sheet.read_active(client)
    if not existing_kws:
        kw_sheet.seed(client, config["default_keywords"])
        print(f"[Keywords] Seeded {len(config['default_keywords'])} default keywords")

    # ------------------------------------------------------------------
    # 3. Read active keywords
    # ------------------------------------------------------------------
    keywords = kw_sheet.read_active(client)
    if not keywords:
        keywords = config["default_keywords"]
    print(f"[Keywords] {len(keywords)} active keywords")

    # ------------------------------------------------------------------
    # 4. Scrape job boards
    # ------------------------------------------------------------------
    from scrapers.greenhouse import GreenhouseScraper
    from scrapers.linkedin import LinkedInScraper

    search_cfg = config["search"]
    # Env var from Telegram bot overrides config.yaml
    location = os.getenv("SEARCH_LOCATION") or search_cfg["location"]
    days = search_cfg["date_posted_days"]
    scrape_limit = search_cfg["daily_limit"]
    print(f"[Config] Location: {location}")
    greenhouse_boards = [c["greenhouse_board"] for c in config.get("greenhouse_companies", [])]

    raw_jobs = []
    for scraper in [
        LinkedInScraper(),
        GreenhouseScraper(greenhouse_boards),
    ]:
        remaining = scrape_limit - len(raw_jobs)
        if remaining <= 0:
            print(f"[{scraper.SOURCE}] Skipped — limit of {scrape_limit} reached")
            break
        print(f"[{scraper.SOURCE}] Searching… (need {remaining} more)")
        try:
            found = scraper.search(keywords, location, days, limit=remaining)
            print(f"[{scraper.SOURCE}] {len(found)} jobs found")
            raw_jobs.extend(found)
        except Exception as exc:
            print(f"[{scraper.SOURCE}] Failed: {exc}")

    # ------------------------------------------------------------------
    # 5. Dedup against cache + existing sheet URLs
    # ------------------------------------------------------------------
    sheet_urls = jobs_sheet.existing_urls(client)
    all_seen = processed_urls | sheet_urls
    new_jobs = filter_new(raw_jobs, all_seen)
    print(f"[Dedup] {len(raw_jobs)} total → {len(new_jobs)} new")

    if not new_jobs:
        print("[Done] No new jobs to process.")
        return

    # ------------------------------------------------------------------
    # 6. Affinity scoring → top N
    # ------------------------------------------------------------------
    from scoring.affinity import score_jobs

    daily_limit = config["search"]["daily_limit"]
    min_score = config["scoring"]["min_score"]
    model = config["scoring"]["model"]

    print(f"[Scoring] Scoring {len(new_jobs)} jobs…")
    scored = score_jobs(new_jobs, cv_text, model=model)
    scored = [j for j in scored if j.affinity_score >= min_score]
    top_jobs = sorted(scored, key=lambda j: j.affinity_score, reverse=True)[:daily_limit]
    print(f"[Scoring] Top {len(top_jobs)} jobs (score ≥ {min_score})")

    # ------------------------------------------------------------------
    # 7. Company dedup + link
    # ------------------------------------------------------------------
    for job in top_jobs:
        company = companies_sheet.find_or_create(
            client,
            name=job.company_name,
            website="",
            source=job.source,
        )
        job.company_id = company.company_id

    # ------------------------------------------------------------------
    # 8. Write to Google Sheets
    # ------------------------------------------------------------------
    jobs_sheet.append_jobs(client, top_jobs)
    companies_sheet.update_job_counts(client)
    print(f"[Sheets] Wrote {len(top_jobs)} jobs")

    # ------------------------------------------------------------------
    # 9. Update dedup cache — add all scraped URLs so junk isn't re-processed
    # ------------------------------------------------------------------
    all_scraped_urls = {j.job_url for j in new_jobs}
    save(processed_urls | all_scraped_urls)
    print(f"[Done] Finished. {len(top_jobs)} jobs added to sheet.")
    _notify_telegram(len(top_jobs), location)


def _notify_telegram(jobs_count: int, location: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return
    import httpx
    text = (
        f"✅ Поиск завершён!\n"
        f"📍 Локация: {location}\n"
        f"💼 Новых вакансий: {jobs_count}\n"
        f"📊 Открой таблицу: https://docs.google.com/spreadsheets/d/{os.getenv('GOOGLE_SHEET_ID')}"
    )
    try:
        httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
    except Exception:
        pass


def _load_config() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with config_path.open() as f:
        return yaml.safe_load(f)



if __name__ == "__main__":
    run()
