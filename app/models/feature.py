"""Spatial feature model with geometry storage."""

from datetime import datetime
from typing import TYPE_CHECKING

from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.dataset import DatasetVersion


class Feature(Base):
    """Spatial feature with geometry and attributes."""

    __tablename__ = "features"

    id = Column(Integer, primary_key=True, index=True)
    dataset_version_id = Column(Integer, ForeignKey("dataset_versions.id"), nullable=False)
    feature_id = Column(String(255), nullable=True, index=True)  # Original ID from source
    geometry = Column(
        Geometry(geometry_type="GEOMETRY", srid=4326),
        nullable=False,
    )
    attributes_json = Column(Text, nullable=True)  # JSON key-value attributes
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        # Spatial index for bounding box and intersection queries
        Index(
            "ix_features_geometry",
            "geometry",
            postgresql_using="gist",
        ),
        Index("ix_features_dataset_version", "dataset_version_id"),
    )

    dataset_version = relationship("DatasetVersion", back_populates="features")
