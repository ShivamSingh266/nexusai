"""add job provenance and normalized locations

Revision ID: b0c1d2e3f4a5
Revises: d1e2f3a4b5c6
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b0c1d2e3f4a5"
down_revision: Union[str, Sequence[str], None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("posting_time_type", sa.String(length=50), nullable=True))
    op.add_column("jobs", sa.Column("posted_date", sa.String(length=50), nullable=True))
    op.add_column("jobs", sa.Column("anticipated_start_min", sa.String(length=50), nullable=True))
    op.add_column("jobs", sa.Column("anticipated_start_max", sa.String(length=50), nullable=True))
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.create_unique_constraint("uq_jobs_source_source_job_id", ["source", "source_job_id"])

    op.create_table(
        "job_source_observations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("artifact_sha256", sa.String(length=64), nullable=False),
        sa.Column("csv_record_number", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column("source_job_id", sa.String(length=64), nullable=True),
        sa.Column("pipeline_version", sa.String(length=128), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("pipeline_run_id", sa.String(length=128), nullable=True),
        sa.Column("source_status", sa.String(length=32), nullable=True),
        sa.Column("job_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("artifact_sha256", "csv_record_number", name="uq_job_source_observations_physical_row"),
    )
    op.create_index("ix_job_source_observations_artifact_sha256", "job_source_observations", ["artifact_sha256"])
    op.create_index("ix_job_source_observations_source", "job_source_observations", ["source"])
    op.create_index("ix_job_source_observations_source_job_id", "job_source_observations", ["source_job_id"])
    op.create_index("ix_job_source_observations_job_id", "job_source_observations", ["job_id"])

    op.create_table(
        "job_location_observations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("district", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "district", name="uq_job_location_observations_job_district"),
    )
    op.create_index("ix_job_location_observations_job_id", "job_location_observations", ["job_id"])


def downgrade() -> None:
    op.drop_index("ix_job_location_observations_job_id", table_name="job_location_observations")
    op.drop_table("job_location_observations")
    op.drop_index("ix_job_source_observations_job_id", table_name="job_source_observations")
    op.drop_index("ix_job_source_observations_source_job_id", table_name="job_source_observations")
    op.drop_index("ix_job_source_observations_source", table_name="job_source_observations")
    op.drop_index("ix_job_source_observations_artifact_sha256", table_name="job_source_observations")
    op.drop_table("job_source_observations")
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.drop_constraint("uq_jobs_source_source_job_id", type_="unique")
    op.drop_column("jobs", "anticipated_start_max")
    op.drop_column("jobs", "anticipated_start_min")
    op.drop_column("jobs", "posted_date")
    op.drop_column("jobs", "posting_time_type")