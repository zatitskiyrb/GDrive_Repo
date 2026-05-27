from __future__ import annotations

import hashlib
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Company(BaseModel):
    company_id: str
    company_name: str
    company_website: str = ""
    source: str
    date_added: date = Field(default_factory=date.today)
    total_jobs: int = 1
    notes: str = ""

    @classmethod
    def create(cls, name: str, website: str, source: str) -> "Company":
        company_id = hashlib.md5(name.lower().strip().encode()).hexdigest()[:12]
        return cls(
            company_id=company_id,
            company_name=name,
            company_website=website,
            source=source,
        )


class Job(BaseModel):
    job_id: str
    job_title: str
    company_name: str
    company_id: str = ""
    job_url: str
    source: str
    location: str = ""
    date_posted: str = ""
    employment_type: str = ""
    affinity_score: int = 0
    match_reasons: list[str] = Field(default_factory=list)
    gap_reasons: list[str] = Field(default_factory=list)
    job_description: str = ""
    date_added: date = Field(default_factory=date.today)

    @field_validator("affinity_score")
    @classmethod
    def clamp_score(cls, v: int) -> int:
        return max(0, min(100, v))

    @classmethod
    def create(cls, *, job_url: str, job_title: str, company_name: str, source: str, **kwargs) -> "Job":
        job_id = hashlib.md5(job_url.encode()).hexdigest()[:12]
        return cls(
            job_id=job_id,
            job_url=job_url,
            job_title=job_title,
            company_name=company_name,
            source=source,
            **kwargs,
        )


class AffinityResult(BaseModel):
    score: int
    match_reasons: list[str] = Field(default_factory=list)
    gap_reasons: list[str] = Field(default_factory=list)

    @field_validator("score")
    @classmethod
    def clamp_score(cls, v: int) -> int:
        return max(0, min(100, v))


class Keyword(BaseModel):
    keyword: str
    active: bool = True
    date_added: date = Field(default_factory=date.today)
    notes: str = ""
