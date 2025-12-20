# Enterprise Geospatial Intelligence Platform — Architecture

## Executive Summary

This platform is designed as enterprise-grade geospatial infrastructure suitable for state environmental agencies, utility companies, and emergency management departments. It provides versioned dataset management, spatial feature storage, spatial query APIs, an upload/ingestion pipeline, spatial processing, and role-based security—all built on free and open-source components.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                       │
│  QGIS │ Web Dashboard │ Mobile │ External Systems (OGC WMS/WFS)              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        API GATEWAY / REST LAYER                              │
│  FastAPI │ JWT Auth │ RBAC │ Rate Limiting │ Request Validation              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌──────────────────────┐  ┌──────────────────┐  ┌────────────────────────────┐
│   PostgreSQL         │  │   Redis          │  │   GeoServer                 │
│   + PostGIS          │  │   (Celery Queue) │  │   WMS / WFS / WCS           │
│   Spatial Indexes    │  │   Job State      │  │   OGC Services              │
│   Row-Level Security │  │   Caching        │  │   Feature Services           │
└──────────────────────┘  └──────────────────┘  └────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ASYNC WORKER LAYER                                    │
│  Celery Workers │ Shapefile Ingestion │ CRS Reprojection │ Bulk Insert       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### 1. Dataset Ingestion Flow

```
Upload (.zip shapefile) → Validate → Extract → CRS Check → Reproject to EPSG:4326
    → Geometry Validation → Bulk Insert → Spatial Index Update → Audit Log
```

### 2. Spatial Query Flow

```
GET /v1/features?bbox=... → Parse BBOX → PostGIS ST_MakeEnvelope
    → Spatial Index Seek → Paginate → GeoJSON Response
```

### 3. Processing Job Flow

```
POST /v1/process/buffer → Validate Input → Enqueue Celery Task
    → Worker Executes → PostGIS ST_Buffer → Store Result → Notify
```

---

## Security Model

- **JWT Authentication**: Stateless tokens with configurable expiry
- **RBAC**: `admin`, `analyst`, `public` roles with distinct permissions
- **Row-Level Security**: Dataset-level access control (extensible)
- **Audit Logging**: All dataset changes, uploads, and processing jobs logged

---

## Scalability Considerations

- **Spatial Indexing**: GIST indexes on all geometry columns
- **Partitioning**: Features table partitioned by `dataset_version_id`
- **Pagination**: Limit/offset with configurable max page size
- **Async Jobs**: Long-running operations offloaded to Celery
- **Connection Pooling**: SQLAlchemy pool with configurable size

---

## Technology Rationale

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Database | PostgreSQL + PostGIS | Industry standard for spatial; RLS; mature |
| API | FastAPI | Async, OpenAPI, Pydantic validation |
| Queue | Redis + Celery | Proven async job processing |
| GIS Server | GeoServer | OGC-compliant; WMS/WFS/WCS; free |
| Geometry | GeoAlchemy2, Shapely | Python spatial stack |
