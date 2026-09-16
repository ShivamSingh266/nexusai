"""Idempotent importer for the processed market jobs artifact.

This module imports jobs only. It deliberately does not import the resolved
job-skill artifact; that is a separate phase with a separate ID audit.
"""

from __future__ import annotations

import csv
import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.job import Job
from app.models.job_observation import JobLocationObservation, JobSourceObservation

MARKET_COMPANY_SUFFIX = " (Market Data)"
EXPECTED_JOBS_SHA256 = "6048cb4b2dcbd616695fa9ed350be6847170059d2e65e0da079c70b3c78dfab3"
EXPECTED_JOBS_ROWS = 27824
EXPECTED_JOBS_FIELDS = [
    "id", "title", "company", "description", "district", "sector", "exp_min",
    "exp_max", "salary_min", "salary_max", "mode", "source", "posting_time_type",
    "posted_date", "anticipated_start_min", "anticipated_start_max", "status",
]
PIPELINE_VERSION = "market-jobs-import-v1"


@dataclass(frozen=True)
class MarketImportResult:
    active_rows: int
    distinct_source_jobs: int
    created_jobs: int
    updated_jobs: int
    created_companies: int
    skipped_rows: int
    created_observations: int


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


def _artifact_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def _validate_artifact(
    path: Path,
    *,
    expected_sha256: str | None,
    expected_row_count: int | None,
) -> list[tuple[int, dict[str, str]]]:
    if not path.exists():
        raise FileNotFoundError(f"Market jobs artifact not found: {path}")
    digest = _artifact_sha256(path)
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError(f"Unexpected jobs artifact SHA-256: {digest}")
    with path.open(newline="", encoding="utf-8-sig") as jobs_file:
        reader = csv.DictReader(jobs_file)
        if reader.fieldnames != EXPECTED_JOBS_FIELDS:
            raise ValueError(f"Unexpected jobs artifact header: {reader.fieldnames}")
        rows = [(record_number, row) for record_number, row in enumerate(reader, 1)]
    if expected_row_count is not None and len(rows) != expected_row_count:
        raise ValueError(f"Unexpected jobs artifact row count: {len(rows)}")
    return rows


def import_market_jobs(
    db: Session,
    jobs_path: Path | None = None,
    *,
    expected_sha256: str | None = EXPECTED_JOBS_SHA256,
    expected_row_count: int | None = EXPECTED_JOBS_ROWS,
    pipeline_version: str = PIPELINE_VERSION,
    pipeline_run_id: str | None = None,
) -> MarketImportResult:
    """Validate and import jobs.csv, retaining every physical source row."""
    path = jobs_path or default_jobs_path()
    physical_rows = _validate_artifact(
        path,
        expected_sha256=expected_sha256,
        expected_row_count=expected_row_count,
    )
    active_rows = [item for item in physical_rows if (_text(item[1], "status") or "").casefold() == "active"]
    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    skipped_rows = 0
    for _, row in active_rows:
        source = _text(row, "source")
        source_job_id = _text(row, "id")
        if source is None or source_job_id is None:
            skipped_rows += 1
            continue
        grouped.setdefault((source, source_job_id), []).append(row)
    created_jobs = 0
    updated_jobs = 0
    created_companies = 0
    created_observations = 0
    company_cache: dict[str, Company] = {}
    jobs_by_identity: dict[tuple[str, str], Job] = {}

    try:
        for identity in sorted(grouped):
            source, source_job_id = identity
            rows = grouped[identity]
            company_name = _first_value(rows, "company")
            if company_name is None:
                skipped_rows += 1
                continue
            company_key = company_name.casefold()
            company = company_cache.get(company_key)
            if company is None:
                company, created = _find_company(db, company_name, sector=_first_value(rows, "sector"))
                company_cache[company_key] = company
                created_companies += int(created)
            districts = sorted({_text(row, "district") for row in rows if _text(row, "district")}, key=str.casefold)
            values = {
                "company_id": company.id,
                "title": _first_value(rows, "title") or "Untitled Market Job",
                "description": _first_value(rows, "description"),
                "location": districts[0] if len(districts) == 1 else None,
                "work_mode": _normalize_mode(_first_value(rows, "mode")),
                "experience_min": _first_float(rows, "exp_min"),
                "experience_max": _first_float(rows, "exp_max"),
                "salary_min": _first_float(rows, "salary_min"),
                "salary_max": _first_float(rows, "salary_max"),
                "status": "published", "source_job_id": source_job_id, "source": source,
                "sector": _first_value(rows, "sector"),
                "posting_time_type": _first_value(rows, "posting_time_type"),
                "posted_date": _first_value(rows, "posted_date"),
                "anticipated_start_min": _first_value(rows, "anticipated_start_min"),
                "anticipated_start_max": _first_value(rows, "anticipated_start_max"),
            }
            job = db.scalar(select(Job).where(Job.source == source, Job.source_job_id == source_job_id))
            if job is None:
                job = Job(**values)
                db.add(job)
                db.flush()
                created_jobs += 1
            else:
                for field, value in values.items():
                    setattr(job, field, value)
                updated_jobs += 1
            jobs_by_identity[identity] = job
            for district in districts:
                if db.scalar(select(JobLocationObservation).where(JobLocationObservation.job_id == job.id, JobLocationObservation.district == district)) is None:
                    db.add(JobLocationObservation(job_id=job.id, district=district))

        for record_number, row in physical_rows:
            source = _text(row, "source")
            source_job_id = _text(row, "id")
            identity = (source, source_job_id) if source and source_job_id else None
            job = jobs_by_identity.get(identity) if identity else None
            if job is None and identity:
                job = db.scalar(select(Job).where(Job.source == source, Job.source_job_id == source_job_id))
            existing = db.scalar(select(JobSourceObservation).where(JobSourceObservation.artifact_sha256 == _artifact_sha256(path), JobSourceObservation.csv_record_number == record_number))
            if existing is None:
                db.add(JobSourceObservation(
                    artifact_sha256=_artifact_sha256(path), csv_record_number=record_number,
                    source=source, source_job_id=source_job_id, pipeline_version=pipeline_version,
                    pipeline_run_id=pipeline_run_id, source_status=_text(row, "status"),
                    job_id=job.id if job else None,
                ))
                created_observations += 1
        db.commit()
    except Exception:
        db.rollback()
        raise
    return MarketImportResult(
        active_rows=len(active_rows),
        distinct_source_jobs=len(grouped),
        created_jobs=created_jobs,
        updated_jobs=updated_jobs,
        created_companies=created_companies,
        skipped_rows=skipped_rows,
        created_observations=created_observations,
    )


if __name__ == "__main__":
    from app.db.session import SessionLocal

    with SessionLocal() as session:
        result = import_market_jobs(session)
    print(result)
