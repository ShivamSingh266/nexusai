"""Tests for the isolated, idempotent market-job importer."""

import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.seed_market_jobs import import_market_jobs
from app.models.company import Company
from app.models.job import Job
from app.models.user import Role, User


FIELDS = [
    "id",
    "title",
    "company",
    "description",
    "district",
    "sector",
    "exp_min",
    "exp_max",
    "salary_min",
    "salary_max",
    "mode",
    "source",
    "posting_time_type",
    "posted_date",
    "anticipated_start_min",
    "anticipated_start_max",
    "status",
]


def make_session() -> tuple[Session, object]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)(), engine


def write_jobs_csv(path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as jobs_file:
        writer = csv.DictWriter(jobs_file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def row(**overrides: str) -> dict[str, str]:
    values = {field: "" for field in FIELDS}
    values.update(
        {
            "id": "100000000001",
            "title": "Data Engineer",
            "company": "Acme",
            "district": "Pune",
            "sector": "IT/Software - Data & AI",
            "exp_min": "2",
            "exp_max": "5",
            "salary_min": "50000",
            "salary_max": "90000",
            "mode": "Work From Home",
            "source": "naukri:indian-job-market-dataset-2025",
            "status": "active",
        }
    )
    values.update(overrides)
    return values


def test_import_deduplicates_locations_maps_fields_and_is_idempotent(tmp_path):
    path = tmp_path / "jobs.csv"
    write_jobs_csv(
        path,
        [
            row(district="Pune"),
            row(district="Mumbai"),
            row(id="100000000002", title="Ignored inactive", status="closed"),
        ],
    )
    db, engine = make_session()
    try:
        existing_company = Company(company_name="Acme")
        db.add(existing_company)
        db.commit()

        first = import_market_jobs(db, path)
        assert first.active_rows == 2
        assert first.distinct_source_jobs == 1
        assert first.created_jobs == 1
        assert first.created_companies == 0

        imported = db.query(Job).one()
        assert imported.id != 100000000001
        assert imported.source_job_id == "100000000001"
        assert imported.source == "naukri:indian-job-market-dataset-2025"
        assert imported.status == "published"
        assert imported.company_id == existing_company.id
        assert imported.location == "Mumbai | Pune"
        assert imported.work_mode == "remote"
        assert imported.sector == "IT/Software - Data & AI"
        assert float(imported.experience_min) == 2
        assert float(imported.salary_max) == 90000

        second = import_market_jobs(db, path)
        assert second.created_jobs == 0
        assert second.updated_jobs == 1
        assert db.query(Job).count() == 1
    finally:
        db.close()
        engine.dispose()


def test_import_creates_missing_company_without_recruiter_and_reuses_it(tmp_path):
    path = tmp_path / "jobs.csv"
    write_jobs_csv(path, [row(company="New Market Company")])
    db, engine = make_session()
    try:
        result = import_market_jobs(db, path)
        assert result.created_companies == 1
        company = db.query(Company).one()
        assert company.company_name == "New Market Company (Market Data)"
        assert company.recruiters == []
        assert db.query(Job).one().company_id == company.id

        rerun = import_market_jobs(db, path)
        assert rerun.created_companies == 0
        assert db.query(Company).count() == 1
    finally:
        db.close()
        engine.dispose()


def test_recruiter_company_is_not_used_for_imported_jobs(tmp_path):
    path = tmp_path / "jobs.csv"
    write_jobs_csv(path, [row(company="Recruiter Company")])
    db, engine = make_session()
    try:
        role = Role(name="recruiter", description="Recruiter")
        company = Company(company_name="Recruiter Company")
        db.add_all([role, company])
        db.flush()
        db.add(
            User(
                email="recruiter@example.com",
                password_hash="test-hash",
                full_name="Recruiter",
                role_id=role.id,
                company_id=company.id,
            )
        )
        db.commit()

        result = import_market_jobs(db, path)
        assert result.created_companies == 1
        imported_job = db.query(Job).one()
        assert imported_job.company_id != company.id
        assert db.get(Company, imported_job.company_id).company_name == "Recruiter Company (Market Data)"
        assert db.query(Job).filter(Job.company_id == company.id).count() == 0
    finally:
        db.close()
        engine.dispose()


def test_null_source_fields_remain_null_and_existing_jobs_are_untouched(tmp_path):
    path = tmp_path / "jobs.csv"
    write_jobs_csv(
        path,
        [
            row(
                id="100000000003",
                company="Null Fields",
                district="",
                sector="",
                exp_min="",
                exp_max="",
                salary_min="",
                salary_max="",
                mode="Unknown Mode",
                source="",
            )
        ],
    )
    db, engine = make_session()
    try:
        company = Company(company_name="Existing Recruiter Company")
        db.add(company)
        db.flush()
        existing = Job(company_id=company.id, title="Recruiter Created Job")
        db.add(existing)
        db.commit()
        existing_id = existing.id

        import_market_jobs(db, path)
        imported = db.query(Job).filter(Job.source_job_id == "100000000003").one()
        assert imported.location is None
        assert imported.sector is None
        assert imported.source is None
        assert imported.experience_min is None
        assert imported.experience_max is None
        assert imported.salary_min is None
        assert imported.salary_max is None
        assert imported.work_mode is None
        assert db.get(Job, existing_id).title == "Recruiter Created Job"
        assert db.get(Job, existing_id).source_job_id is None
    finally:
        db.close()
        engine.dispose()
