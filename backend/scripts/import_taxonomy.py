import csv
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

# Allow running this file directly from backend/
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db.session import SessionLocal
from app.models.canonical_skill import CanonicalSkill, SkillAlias


SKILLS_CSV = ROOT / "data" / "skills_2.csv"
ALIASES_CSV = ROOT / "data" / "skill_aliases_2.csv"


def normalize(value: str) -> str:
    """Normalize names/aliases using the taxonomy normalization rule."""
    return " ".join(value.strip().lower().split())


def parse_bool_status(status: str) -> bool:
    """Map CSV status to the database is_active field."""
    return status.strip().lower() == "active"


def import_skills(session: Session) -> int:
    """Import canonical skills from skills_2.csv."""
    count = 0

    with SKILLS_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            skill_id = row["skill_id"].strip()

            existing = session.get(CanonicalSkill, skill_id)

            if existing:
                existing.canonical_name = row["canonical_name"].strip()
                existing.normalized_name = normalize(row["normalized_name"])
                existing.category = row["category"].strip()
                existing.source = row["source"].strip()
                existing.taxonomy_version = row["taxonomy_version"].strip()
                existing.esco_uri = row["esco_uri"].strip() or None
                existing.is_active = parse_bool_status(row["status"])
            else:
                skill = CanonicalSkill(
                    skill_id=skill_id,
                    canonical_name=row["canonical_name"].strip(),
                    normalized_name=normalize(row["normalized_name"]),
                    category=row["category"].strip(),
                    source=row["source"].strip(),
                    taxonomy_version=row["taxonomy_version"].strip(),
                    esco_uri=row["esco_uri"].strip() or None,
                    is_active=parse_bool_status(row["status"]),
                )
                session.add(skill)

            count += 1

    session.flush()
    return count


def import_aliases(session: Session) -> int:
    """Import skill aliases from skill_aliases_2.csv."""
    count = 0

    with ALIASES_CSV.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            alias = row["alias"].strip()
            skill_id = row["skill_id"].strip()
            normalized_alias = normalize(alias)
            confidence = float(row["confidence"])

            existing = session.scalar(
                select(SkillAlias).where(
                    SkillAlias.normalized_alias == normalized_alias,
                    SkillAlias.skill_id == skill_id,
                )
            )

            if existing:
                existing.alias = alias
                existing.confidence = confidence
            else:
                session.add(
                    SkillAlias(
                        alias=alias,
                        normalized_alias=normalized_alias,
                        skill_id=skill_id,
                        confidence=confidence,
                    )
                )

                # Flush immediately so duplicate rows later in the
                # same CSV are detected by the database session.
                session.flush()

            count += 1

    return count


def main() -> None:
    if not SKILLS_CSV.exists():
        raise FileNotFoundError(f"Missing file: {SKILLS_CSV}")

    if not ALIASES_CSV.exists():
        raise FileNotFoundError(f"Missing file: {ALIASES_CSV}")

    with SessionLocal() as session:
        try:
            skill_count = import_skills(session)
            alias_count = import_aliases(session)

            session.commit()

            print(f"Canonical skills processed: {skill_count}")
            print(f"Skill aliases processed: {alias_count}")
            print("Taxonomy import completed successfully.")

        except Exception:
            session.rollback()
            raise


if __name__ == "__main__":
    main()