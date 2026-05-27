import json
from pathlib import Path

_CACHE_PATH = Path(__file__).parent.parent / "data" / "processed_urls.json"


def load() -> set[str]:
    if not _CACHE_PATH.exists():
        return set()
    with _CACHE_PATH.open() as f:
        return set(json.load(f))


def save(urls: set[str]) -> None:
    _CACHE_PATH.parent.mkdir(exist_ok=True)
    with _CACHE_PATH.open("w") as f:
        json.dump(sorted(urls), f, indent=2)


def filter_new(jobs: list, processed: set[str]) -> list:
    return [j for j in jobs if j.job_url not in processed]
