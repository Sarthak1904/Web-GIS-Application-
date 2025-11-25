"""Add spatial indexes and schema optimizations.

Revision ID: 002
Revises: 001
Create Date: 2025-12-15 14:30:00

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy.sql import text

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add composite index for dataset version lookups (partial: non-deleted only)
    op.create_index(
        "ix_dataset_versions_status_created",
        "dataset_versions",
        ["status", "created_at"],
        postgresql_where=text("deleted_at IS NULL"),
    )
    # Add index for processing job lookups by type
    op.create_index(
        "ix_processing_jobs_job_type_status",
        "processing_jobs",
        ["job_type", "status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_processing_jobs_job_type_status",
        table_name="processing_jobs",
    )
    op.drop_index(
        "ix_dataset_versions_status_created",
        table_name="dataset_versions",
    )
