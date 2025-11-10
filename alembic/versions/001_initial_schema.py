"""Initial schema — users, roles, datasets, features, processing, audit.

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable PostGIS if not already
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # Roles
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("permissions", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
    )
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)

    # Users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=True),
        sa.Column("is_superuser", sa.Boolean(), server_default=sa.text("false"), nullable=True),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("last_login", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    # Datasets
    op.create_table(
        "datasets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_datasets_slug", "datasets", ["slug"], unique=True)
    op.create_index("ix_datasets_name", "datasets", ["name"])

    # Dataset versions
    op.create_table(
        "dataset_versions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("dataset_id", sa.Integer(), sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "ingesting", "active", "archived", "deprecated", name="datasetlifecyclestatus"),
            server_default="draft",
            nullable=False,
        ),
        sa.Column("crs", sa.String(50), server_default="EPSG:4326", nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_dataset_versions_dataset_version",
        "dataset_versions",
        ["dataset_id", "version"],
        unique=True,
    )

    # Features (with geometry)
    op.create_table(
        "features",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("dataset_version_id", sa.Integer(), sa.ForeignKey("dataset_versions.id"), nullable=False),
        sa.Column("feature_id", sa.String(255), nullable=True),
        sa.Column("geometry", Geometry(geometry_type="GEOMETRY", srid=4326), nullable=False),
        sa.Column("attributes_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
    )
    op.create_index(
        "ix_features_geometry",
        "features",
        ["geometry"],
        postgresql_using="gist",
    )
    op.create_index("ix_features_dataset_version", "features", ["dataset_version_id"])
    op.create_index("ix_features_feature_id", "features", ["feature_id"])

    # Processing jobs
    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "job_type",
            sa.Enum("ingestion", "buffer", "spatial_join", "risk_score", "topology_validate", name="processingjobtype"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("pending", "running", "completed", "failed", "cancelled", name="processingjobstatus"),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("initiated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("parameters_json", sa.Text(), nullable=True),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_processing_jobs_celery_task_id", "processing_jobs", ["celery_task_id"])
    op.create_index("ix_processing_jobs_status_created", "processing_jobs", ["status", "created_at"])

    # Audit logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "action",
            sa.Enum(
                "dataset_create", "dataset_update", "dataset_delete",
                "version_create", "version_update",
                "upload_start", "upload_complete", "upload_failed",
                "processing_start", "processing_complete", "processing_failed",
                "user_login", "user_logout",
                name="auditaction",
            ),
            nullable=False,
        ),
        sa.Column("entity_type", sa.String(100), nullable=True),
        sa.Column("entity_id", sa.String(100), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created", "audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])

    # Seed default roles
    op.execute("""
        INSERT INTO roles (name, description) VALUES
        ('admin', 'Full system access'),
        ('analyst', 'Can create/edit datasets and run processing'),
        ('public', 'Read-only access to published datasets')
    """)


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("processing_jobs")
    op.drop_table("features")
    op.drop_table("dataset_versions")
    op.drop_table("datasets")
    op.drop_table("users")
    op.drop_table("roles")
    op.execute("DROP TYPE IF EXISTS auditaction")
    op.execute("DROP TYPE IF EXISTS processingjobstatus")
    op.execute("DROP TYPE IF EXISTS processingjobtype")
    op.execute("DROP TYPE IF EXISTS datasetlifecyclestatus")
