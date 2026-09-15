"""Idempotent importer for the processed market jobs artifact.

This module imports jobs only. It deliberately does not import the resolved
job-skill artifact; that is a separate phase with a separate ID audit.
"""

from __future__ import annotations

import csv
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.job import Job

MARKET_COMPANY_SUFFIX = " (Market Data)"


@dataclass(frozen=True)
class MarketImportResult:
    active_rows: int
    distinct_source_jobs: int
    created_jobs: int
    updated_jobs: int
    created_companies: int
    skipped_rows: int


def default_jobs_path() -> Path:
    root = Path(os.environ.get("NEXUSAI_ROOT", Path(__file__).resolve().parents[3]))
    return root / "datasets" / "processed" / "jobs.csv"


def _text(row: dict[str, str], field: str) -> str | None:
    value = (row.get(field) or "").strip()
    return value or None


def _first_float(rows: list[dict[str, str]], field: str) -> float | None:
    values = sorted(
        {
            value
            for row in rows
            if (value := _text(row, field)) is not None
        }
    )
    if not values:
        return None
    try:
        return float(values[0])
    except ValueError:
        return None


def _normalize_mode(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = re.sub(r"[\s_-]+", " ", value.casefold()).strip()
    if normalized in {"remote", "work from home", "wfh"}:
        return "remote"
    if normalized in {"hybrid"}:
        return "hybrid"
    if normalized in {"onsite", "on site", "in office", "office"}:
        return "onsite"
    return None


def _combined_location(rows: Iterable[dict[str, str]]) -> str | None:
    districts = sorted(
        {
            district
            for row in rows
            if (district := _text(row, "district")) is not None
        },
        key=str.casefold,
    )
    return " | ".join(districts) if districts else None


def _first_value(rows: list[dict[str, str]], field: str) -> str | None:
    values = sorted(
        {value for row in rows if (value := _text(row, field)) is not None},
        key=str.casefold,
    )
    return values[0] if values else None


def _company_has_recruiters(company: Company) -> bool:
    return bool(company.recruiters)


def _find_company(
    db: Session,
    company_name: str,
    *,
    sector: str | None,
) -> tuple[Company, bool]:
    """Resolve a company without attaching imported jobs to recruiters."""
    normalized = company_name.casefold()
    companies = db.scalars(select(Company).order_by(Company.id)).all()
    exact = [company for company in companies if company.company_name.casefold() == normalized]
    for company in exact:
        if not _company_has_recruiters(company):
            return company, False

    base_name = company_name + MARKET_COMPANY_SUFFIX
    candidate_name = base_name
    suffix = 2
    while True:
        matching = [
            company for company in companies
            if company.company_name.casefold() == candidate_name.casefold()
        ]
        if not matching:
            company = Company(company_name=candidate_name, industry=sector)
            db.add(company)
            db.flush()
            return company, True
        if not any(_company_has_recruiters(company) for company in matching):
            return matching[0], False
        candidate_name = f"{base_name} {suffix}"
        suffix += 1


def _rows_by_source_id(path: Path) -> tuple[int, dict[str, list[dict[str, str]]], int]:
    if not path.exists():
        raise FileNotFoundError(f"Market jobs artifact not found: {path}")

    active_rows = 0
    skipped_rows = 0
    grouped: dict[str, list[dict[str, str]]] = {}
    with path.open(newline="", encoding="utf-8-sig") as jobs_file:
        for row in csv.DictReader(jobs_file):
            if (_text(row, "status") or "").casefold() != "active":
                continue
            active_rows += 1
            source_job_id = _text(row, "id")
            if source_job_id is None:
                skipped_rows += 1
                continue
            grouped.setdefault(source_job_id, []).append(row)
    return active_rows, grouped, skipped_rows


def import_market_jobs(db: Session, jobs_path: Path | None = None) -> MarketImportResult:
    """Import active, location-deduplicated market jobs into the database."""
    path = jobs_path or default_jobs_path()
    active_rows, grouped, skipped_rows = _rows_by_source_id(path)
    created_jobs = 0
    updated_jobs = 0
    created_companies = 0
    company_cache: dict[str, Company] = {}

    for source_job_id in sorted(grouped):
        rows = grouped[source_job_id]
        company_name = _first_value(rows, "company")
        if company_name is None:
            skipped_rows += 1
            continue
        company_key = company_name.casefold()
        company = company_cache.get(company_key)
        if company is None:
            company, created = _find_company(
                db,
                company_name,
                sector=_first_value(rows, "sector"),
            )
            company_cache[company_key] = company
            created_companies += int(created)

        first_row = sorted(
            rows,
            key=lambda row: tuple((_text(row, field) or "").casefold() for field in ("title", "description", "source")),
        )[0]
        source = _first_value(rows, "source")
        job = db.scalar(select(Job).where(Job.source_job_id == source_job_id))
        values = {
            "company_id": company.id,
            "title": _first_value(rows, "title") or "Untitled Market Job",
            "description": _first_value(rows, "description"),
            "location": _combined_location(rows),
            "work_mode": _normalize_mode(_first_value(rows, "mode")),
            "experience_min": _first_float(rows, "exp_min"),
            "experience_max": _first_float(rows, "exp_max"),
            "salary_min": _first_float(rows, "salary_min"),
            "salary_max": _first_float(rows, "salary_max"),
            "status": "published",
            "source_job_id": source_job_id,
            "source": source,
            "sector": _first_value(rows, "sector"),
        }
        if job is None:
            db.add(Job(**values))
            created_jobs += 1
        else:
            for field, value in values.items():
                setattr(job, field, value)
            updated_jobs += 1

    db.commit()
    return MarketImportResult(
        active_rows=active_rows,
        distinct_source_jobs=len(grouped),
        created_jobs=created_jobs,
        updated_jobs=updated_jobs,
        created_companies=created_companies,
        skipped_rows=skipped_rows,
    )


if __name__ == "__main__":
    from app.db.session import SessionLocal

    with SessionLocal() as session:
        result = import_market_jobs(session)
    print(result)
