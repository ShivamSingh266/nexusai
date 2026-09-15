from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.user import Role


ROLES = [
    {
        "name": "applicant",
        "description": "Job seeker / candidate using NexusAI",
    },
    {
        "name": "recruiter",
        "description": "Recruiter or hiring organization using NexusAI",
    },
    {
        "name": "government",
        "description": "Government or policy user with authorized access",
    },
    {
        "name": "admin",
        "description": "NexusAI system administrator",
    },
]


def seed_roles() -> None:
    db = SessionLocal()

    try:
        for role_data in ROLES:
            existing_role = db.scalar(
                select(Role).where(Role.name == role_data["name"])
            )

            if existing_role is None:
                db.add(Role(**role_data))

        db.commit()
        print("Roles seeded successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_roles()