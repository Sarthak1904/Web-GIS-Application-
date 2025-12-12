#!/usr/bin/env python3
"""Performance benchmarks for spatial operations.

Run: python scripts/benchmark_spatial.py
"""

import time
from shapely.geometry import Point
from shapely.ops import transform
import pyproj


def benchmark_buffer(n: int = 10000) -> float:
    """Benchmark buffer operations on points."""
    points = [Point(i % 180 - 90, i % 90 - 45) for i in range(n)]
    start = time.perf_counter()
    for p in points:
        p.buffer(0.1)
    return time.perf_counter() - start


def benchmark_reproject(n: int = 1000) -> float:
    """Benchmark CRS reprojection."""
    transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857")
    points = [(i % 180 - 90, i % 90 - 45) for i in range(n)]
    start = time.perf_counter()
    for lon, lat in points:
        transformer.transform(lat, lon)
    return time.perf_counter() - start


def main() -> None:
    """Run benchmarks and print results."""
    print("Spatial Performance Benchmarks")
    print("=" * 40)
    t_buffer = benchmark_buffer(5000)
    print(f"Buffer (5000 points): {t_buffer:.3f}s")
    t_reproj = benchmark_reproject(1000)
    print(f"Reproject (1000 points): {t_reproj:.3f}s")
    print("Done.")


if __name__ == "__main__":
    main()
