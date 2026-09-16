"""Read-only access to committed Member 4 government datasets."""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import settings


DATASET_SOURCE_VERSION = "member4-processed-v1"

class GovernmentDatasetValidationError(ValueError):
    """Raised when a committed government dataset is structurally invalid."""


def _validate_numeric_fields(
    filename: str,
    rows: tuple[dict[str, str], ...],
    fields: tuple[str, ...],
) -> None:
    for row_number, row in enumerate(rows, start=2):
        for field in fields:
            value = row.get(field, "").strip()
            if value:
                try:
                    float(value)
                except ValueError as exc:
                    raise GovernmentDatasetValidationError(
                        f"{filename} contains an invalid numeric value at row {row_number}"
                    ) from exc


def _processed_dir() -> Path:
    return Path(__file__).resolve().parents[3] / settings.PROCESSED_DATA_DIR


@lru_cache(maxsize=4)
def _read_csv(
    filename: str,
    required_columns: tuple[str, ...],
    required_values: tuple[str, ...],
) -> tuple[dict[str, str], ...]:
    path = _processed_dir() / filename
    if not path.is_file():
        raise FileNotFoundError(f"Processed dataset not found: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = tuple(reader.fieldnames or ())
        missing_columns = set(required_columns) - set(columns)
        if missing_columns:
            raise GovernmentDatasetValidationError(
                f"{filename} is missing required columns"
            )
        rows = tuple(reader)
    for row_number, row in enumerate(rows, start=2):
        if any(not row.get(column, "").strip() for column in required_values):
            raise GovernmentDatasetValidationError(
                f"{filename} contains a missing required value at row {row_number}"
            )
    return rows


def read_demand_history(
    *,
    skill_id: str | None = None,
    district_id: str | None = None,
    sector: str | None = None,
) -> list[dict[str, Any]]:
    raw_rows = _read_csv(
            "skill_demand_history.csv",
            (
                "skill_id",
                "district_id",
                "sector",
                "period",
                "current_demand_count",
                "anticipated_demand_count",
                "demand_score",
                "strength_tier",
                "sample_size",
                "recent_growth",
                "source",
            ),
            ("skill_id", "district_id", "sector", "period"),
        )
    _validate_numeric_fields(
        "skill_demand_history.csv",
        raw_rows,
        (
            "current_demand_count",
            "anticipated_demand_count",
            "demand_score",
            "sample_size",
            "recent_growth",
        ),
    )
    rows = list(raw_rows)
    if skill_id:
        rows = [row for row in rows if row["skill_id"] == skill_id]
    if district_id:
        rows = [row for row in rows if row["district_id"] == district_id]
    if sector:
        rows = [row for row in rows if row["sector"] == sector]
    return sorted(
        rows,
        key=lambda row: (row["skill_id"], row["district_id"], row["sector"], row["period"]),
    )


def read_courses(*, skill_id: str | None = None) -> list[dict[str, Any]]:
    courses = {
        row["id"]: row
        for row in _read_csv(
            "courses.csv",
            (
                "id",
                "provider",
                "name",
                "subcategory",
                "level",
                "duration_weeks",
                "credits",
                "source_url",
                "source",
            ),
            ("id", "provider", "name", "source"),
        )
    }
    if skill_id:
        course_ids = {
            row["course_id"]
            for row in _read_csv(
                "course_skills.csv",
                ("course_id", "skill_id", "coverage_level", "confidence"),
                ("course_id", "skill_id"),
            )
            if row["skill_id"] == skill_id
        }
        courses = {course_id: row for course_id, row in courses.items() if course_id in course_ids}
    try:
        return [
            {
                "course_id": row["id"],
                "provider": row["provider"],
                "name": row["name"],
                "subcategory": row["subcategory"],
                "level": row["level"] or None,
                "duration_weeks": int(row["duration_weeks"]) if row["duration_weeks"] else None,
                "credits": float(row["credits"]) if row["credits"] else None,
                "source_url": row["source_url"] or None,
                "source": row["source"],
            }
            for row in sorted(courses.values(), key=lambda item: item["id"])
        ]
    except (TypeError, ValueError) as exc:
        raise GovernmentDatasetValidationError("courses.csv contains an invalid scalar value") from exc


def read_training_gaps(*, skill_id: str | None = None) -> list[dict[str, Any]]:
    rows = list(
        _read_csv(
            "training_gap.csv",
            ("skill_id", "demand_strength_tier", "course_count", "gap_flag"),
            ("skill_id", "demand_strength_tier", "course_count", "gap_flag"),
        )
    )
    for row_number, row in enumerate(rows, start=2):
        if row["gap_flag"].lower() not in {"true", "false"}:
            raise GovernmentDatasetValidationError(
                f"training_gap.csv contains an invalid boolean value at row {row_number}"
            )
    if skill_id:
        rows = [row for row in rows if row["skill_id"] == skill_id]
    try:
        return [
            {
                "skill_id": row["skill_id"],
                "demand_strength_tier": row["demand_strength_tier"],
                "course_count": int(row["course_count"]),
                "gap_flag": row["gap_flag"].lower() == "true",
            }
            for row in sorted(rows, key=lambda item: item["skill_id"])
        ]
    except (TypeError, ValueError) as exc:
        raise GovernmentDatasetValidationError(
            "training_gap.csv contains an invalid scalar value"
        ) from exc
