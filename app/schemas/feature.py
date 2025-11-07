"""Feature and spatial query schemas."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class FeatureResponse(BaseModel):
    """GeoJSON Feature response."""

    type: str = "Feature"
    id: Optional[int] = None
    geometry: dict[str, Any]
    properties: dict[str, Any] = {}


class FeatureCollectionResponse(BaseModel):
    """GeoJSON FeatureCollection response."""

    type: str = "FeatureCollection"
    features: list[FeatureResponse]
    total: Optional[int] = None


class SpatialQueryParams(BaseModel):
    """Spatial query parameters."""

    bbox: Optional[str] = Field(None, description="Comma-separated minx,miny,maxx,maxy (WGS84)")
    intersects: Optional[str] = Field(None, description="WKT geometry for intersection")
    near: Optional[str] = Field(None, description="lon,lat,distance_meters for proximity")
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class BufferRequest(BaseModel):
    """Buffer operation request."""

    dataset_version_id: int
    feature_ids: list[int] = []
    distance_meters: float = Field(..., gt=0, le=100000)
    output_dataset_name: Optional[str] = None


class SpatialJoinRequest(BaseModel):
    """Spatial join request."""

    source_dataset_version_id: int
    target_dataset_version_id: int
    join_type: str = "intersects"
    output_dataset_name: Optional[str] = None


class RiskScoreRequest(BaseModel):
    """Risk scoring request (example)."""

    dataset_version_id: int
    hazard_layer_version_id: int
    weight_hazard: float = 0.6
    weight_exposure: float = 0.4
