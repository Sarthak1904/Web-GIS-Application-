"""Dataset and version models with lifecycle management."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum, Index
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.feature import Feature
    from app.models.user import User


class DatasetLifecycleStatus(str, enum.Enum):
    """Dataset lifecycle states."""

    DRAFT = "draft"
    INGESTING = "ingesting"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class Dataset(Base):
    """Top-level dataset container (logical grouping)."""

    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)  # JSON metadata (ISO 19115, etc.)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    versions = relationship("DatasetVersion", back_populates="dataset", order_by="DatasetVersion.version")


class DatasetVersion(Base):
    """Versioned snapshot of a dataset with spatial data."""

    __tablename__ = "dataset_versions"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    version = Column(Integer, nullable=False)
    status = Column(
        Enum(DatasetLifecycleStatus, values_callable=lambda x: [e.value for e in x]),
        default=DatasetLifecycleStatus.DRAFT,
        nullable=False,
        index=True,
    )
    crs = Column(String(50), default="EPSG:4326", nullable=False)
    metadata_json = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_dataset_versions_dataset_version", "dataset_id", "version", unique=True),
    )

    dataset = relationship("Dataset", back_populates="versions")
    features = relationship("Feature", back_populates="dataset_version", cascade="all, delete-orphan")
