"""Spatial operations service — architectural abstraction for geospatial logic."""

from typing import Any

from shapely.geometry import shape
from shapely.ops import transform
import pyproj


def reproject_geometry(geom: Any, from_crs: str = "EPSG:4326", to_crs: str = "EPSG:3857") -> Any:
    """Reproject geometry between CRS."""
    transformer = pyproj.Transformer.from_crs(from_crs, to_crs)
    return transform(transformer.transform, geom)


def geometry_from_geojson(geojson: dict) -> Any:
    """Create Shapely geometry from GeoJSON dict."""
    return shape(geojson)
