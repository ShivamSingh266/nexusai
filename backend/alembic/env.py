from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from app.core.config import settings
from app.db.base import Base

# Import all models so Alembic can detect them
from app.models.user import Role, User  # noqa: F401
from app.models.applicant_profile import ApplicantProfile  # noqa: F401
from app.models.applicant_skill import ApplicantSkill  # noqa: F401
from app.models.canonical_skill import CanonicalSkill, SkillAlias  # noqa: F401
from app.models.company import Company  # noqa: F401
from app.models.job import Job  # noqa: F401
from app.models.job_skill import JobSkill  # noqa: F401
from app.models.resume import Resume  # noqa: F401
from app.models.roadmap import Roadmap, RoadmapItem  # noqa: F401
from app.models.shortlist import Shortlist  # noqa: F401


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = settings.DATABASE_URL

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(
        config.config_ini_section,
        {},
    )

    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
