"""Dataset and version schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class DatasetVersionBase(BaseModel):
    """Base schema for dataset version."""

    version: int = 1
    crs: str = "EPSG:4326"
    metadata_json: Optional[str] = None


class DatasetVersionCreate(DatasetVersionBase):
    """Create dataset version."""

    dataset_id: int


class DatasetVersionResponse(DatasetVersionBase):
    """Dataset version response."""

    id: int
    dataset_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DatasetBase(BaseModel):
    """Base dataset schema."""

    name: str
    slug: str
    description: Optional[str] = None
    metadata_json: Optional[str] = None


class DatasetCreate(DatasetBase):
    """Create dataset."""

    pass


class DatasetResponse(DatasetBase):
    """Dataset response."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DatasetWithVersions(DatasetResponse):
    """Dataset with versions."""

    versions: list[DatasetVersionResponse] = []
