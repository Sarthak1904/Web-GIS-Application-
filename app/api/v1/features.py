"""Spatial feature query endpoints — bbox, intersects, near."""

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2.functions import ST_Intersects, ST_DWithin, ST_MakeEnvelope, ST_GeomFromText
from geoalchemy2 import WKTElement

from app.core.database import get_db
from app.models.feature import Feature
from app.models.dataset import DatasetVersion, DatasetLifecycleStatus
from app.api.deps import get_current_user_optional
from app.models.user import User
from app.schemas.feature import FeatureResponse, FeatureCollectionResponse

router = APIRouter(prefix="/features", tags=["features"])


def _feature_to_geojson(feature: Feature) -> dict:
    """Convert Feature model to GeoJSON Feature dict."""
    from geoalchemy2.shape import to_shape
    from shapely.geometry import mapping

    geom = to_shape(feature.geometry) if feature.geometry else None
    geometry = mapping(geom) if geom else {"type": "GeometryCollection", "geometries": []}

    import json
    props = json.loads(feature.attributes_json) if feature.attributes_json else {}
    props["id"] = feature.id
    if feature.feature_id:
        props["feature_id"] = feature.feature_id

    return {
        "type": "Feature",
        "id": feature.id,
        "geometry": geometry,
        "properties": props,
    }


@router.get("", response_model=dict)
def query_features(
    dataset_version_id: int = Query(..., description="Dataset version ID"),
    bbox: Optional[str] = Query(None, description="minx,miny,maxx,maxy (WGS84)"),
    intersects: Optional[str] = Query(None, description="WKT geometry"),
    near: Optional[str] = Query(None, description="lon,lat,distance_meters"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[Optional[User], Depends(get_current_user_optional)] = None,
):
    """
    Query features by bbox, intersects, or near.
    Public read for active datasets; auth required for draft/ingesting.
    """
    # Verify dataset version exists and is accessible
    dv = db.query(DatasetVersion).filter(
        DatasetVersion.id == dataset_version_id,
        DatasetVersion.deleted_at.is_(None),
    ).first()

    if not dv:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Dataset version not found")

    # For non-active, require auth
    if dv.status != DatasetLifecycleStatus.ACTIVE and current_user is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Authentication required for this dataset")

    q = db.query(Feature).filter(Feature.dataset_version_id == dataset_version_id)

    if bbox:
        parts = [float(x.strip()) for x in bbox.split(",")]
        if len(parts) != 4:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="bbox must be minx,miny,maxx,maxy")
        minx, miny, maxx, maxy = parts
        envelope = func.ST_MakeEnvelope(minx, miny, maxx, maxy, 4326)
        q = q.filter(func.ST_Intersects(Feature.geometry, envelope))

    elif intersects:
        try:
            wkt = WKTElement(intersects, srid=4326)
            q = q.filter(ST_Intersects(Feature.geometry, wkt))
        except Exception:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Invalid WKT geometry")

    elif near:
        parts = [x.strip() for x in near.split(",")]
        if len(parts) != 3:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="near must be lon,lat,distance_meters")
        lon, lat, dist = float(parts[0]), float(parts[1]), float(parts[2])
        point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        q = q.filter(ST_DWithin(Feature.geometry, point, dist / 111320.0))  # approx meters to degrees

    total = q.count()
    features = q.offset(offset).limit(limit).all()

    return {
        "type": "FeatureCollection",
        "features": [_feature_to_geojson(f) for f in features],
        "total": total,
    }
