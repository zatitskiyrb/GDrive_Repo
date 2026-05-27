from __future__ import annotations

import json

import anthropic

from models.schemas import AffinityResult, Job

_PROMPT = """\
You are a career advisor. Score how well the job matches the candidate's profile.

CANDIDATE PROFILE:
{cv_text}

JOB:
Title: {job_title}
Company: {company_name}
Location: {location}
Description:
{job_description}

Return ONLY valid JSON (no markdown, no explanation):
{{
  "score": <integer 0-100>,
  "match_reasons": ["<reason 1>", "<reason 2>"],
  "gap_reasons": ["<gap 1>"]
}}

Score guide: 80-100 excellent fit, 50-79 good with gaps, 0-49 poor fit.\
"""


def score_jobs(
    jobs: list[Job],
    cv_text: str,
    model: str = "claude-haiku-4-5-20251001",
) -> list[Job]:
    client = anthropic.Anthropic()

    for job in jobs:
        try:
            result = _score_one(client, job, cv_text, model)
            job.affinity_score = result.score
            job.match_reasons = result.match_reasons
            job.gap_reasons = result.gap_reasons
        except Exception as exc:
            print(f"[Scoring] Failed for '{job.job_title}': {exc}")
            job.affinity_score = 0

    return jobs


def _score_one(
    client: anthropic.Anthropic,
    job: Job,
    cv_text: str,
    model: str,
) -> AffinityResult:
    prompt = _PROMPT.format(
        cv_text=cv_text[:3000],
        job_title=job.job_title,
        company_name=job.company_name,
        location=job.location,
        job_description=job.job_description[:2000],
    )

    message = client.messages.create(
        model=model,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        # Extract content between first pair of fences: split gives ["", "json\n{...}\n", ""]
        parts = raw.split("```")
        raw = parts[1].lstrip("json").strip() if len(parts) >= 2 else raw
    if not raw:
        raise ValueError(f"Empty response from model for job '{job.job_title}'")
    data = json.loads(raw)
    return AffinityResult(**data)
