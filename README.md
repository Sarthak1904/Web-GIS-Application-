# Enterprise Geospatial Intelligence Platform

> Production-grade geospatial data infrastructure for government agencies, utilities, and emergency management. Built entirely with free and open-source technologies.

---

## Overview

### What Is This?

A **centralized system for storing, managing, and working with map and location data** — flood zones, utility networks, emergency areas, and more. It replaces scattered shapefiles and manual GIS workflows with a secure, versioned, API-driven platform.

### The Problem

Many organizations today rely on:

- Shapefiles scattered across shared drives
- Desktop-only tools (ArcGIS, QGIS) for every operation
- Manual buffer and spatial join workflows
- No version control, API access, or audit trail

Spatial data stays trapped in files instead of functioning as enterprise infrastructure.

### The Solution

This platform transforms geospatial data from **desktop-based file workflows** into **secure, versioned, API-driven spatial infrastructure**:

| Capability | Description |
|------------|-------------|
| **Storage** | Map layers (points, lines, polygons) in a versioned database with full history |
| **Upload** | Shapefile ingestion with validation, CRS reprojection, and bulk loading |
| **Queries** | "What's in this area?" or "What's near this point?" via REST API |
| **Processing** | Buffer, spatial join, risk scoring, topology validation — automated |
| **Security** | JWT auth, role-based access (admin, analyst, public), immutable audit logs |
| **Integration** | REST APIs, OGC WMS/WFS, token-based access for dashboards and mobile apps |

### Who It's For

Government agencies • Utilities (electric, water, gas) • Emergency management • Environmental planning

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Or: Python 3.11+, Node.js 18+, PostgreSQL 16 with PostGIS, Redis

### Run with Docker

```bash
docker-compose up -d
```

API: `http://localhost:8000` • Docs: `http://localhost:8000/docs`

### Run Frontend Locally

```bash
cd frontend
npm install
npm run dev
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Clients: Web Dashboard (React) • QGIS • External Systems       │
└─────────────────────────────────────────────────────────────────┘
                                    │ HTTPS (JWT)
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  API: FastAPI • JWT Auth • RBAC • OpenAPI                        │
└─────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│ PostgreSQL +   │           │ Redis         │           │ GeoServer     │
│ PostGIS       │           │ Celery Queue  │           │ WMS / WFS     │
└───────┬───────┘           └───────┬───────┘           └───────────────┘
        │                           │
        └───────────────────────────┼───────────────────────────┐
                                    ▼                           │
┌─────────────────────────────────────────────────────────────────┐
│  Celery Workers: Shapefile Ingestion • Buffer • Spatial Join     │
│  Risk Scoring • Topology Validation                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| **API** | FastAPI, Pydantic, JWT, RBAC |
| **Database** | PostgreSQL 16, PostGIS 3.4 |
| **Queue** | Redis, Celery |
| **GIS Server** | GeoServer 2.25 |
| **Geospatial** | GeoAlchemy2, Shapely, GDAL, GeoPandas |

---

## Core Features

1. **Dataset Management** — Versioned datasets, metadata, lifecycle (`draft` → `ingesting` → `active` → `archived`), soft delete
2. **Spatial Storage** — Geometry/geography types, GIST indexes for fast queries
3. **Spatial Query API** — `bbox`, `intersects`, `near` with pagination
4. **Upload Pipeline** — Shapefile ingestion, CRS validation, reprojection to EPSG:4326
5. **Spatial Processing** — Buffer, spatial join, risk scoring, topology validation (async via Celery)
6. **Security** — JWT authentication, role-based access control
7. **Audit Logging** — Immutable logs for dataset changes, uploads, and processing jobs

---

## API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/auth/login` | JWT login |
| POST | `/v1/auth/refresh` | Refresh token |
| GET | `/v1/auth/me` | Current user (Bearer) |

### Datasets & Features

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/v1/datasets` | Admin/Analyst | Create dataset |
| GET | `/v1/datasets` | All | List datasets |
| GET | `/v1/features` | Optional | Spatial query |

### Upload & Processing

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/v1/upload/shapefile` | Admin/Analyst | Upload shapefile |
| POST | `/v1/process/buffer` | Admin/Analyst | Buffer job |
| POST | `/v1/process/spatial-join` | Admin/Analyst | Spatial join |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/metrics-ready` | Readiness probe |

---

## Usage Examples

**Login**

```bash
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

**Create Dataset**

```bash
curl -X POST http://localhost:8000/v1/datasets \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Flood Zones","slug":"flood-zones","description":"FEMA flood hazard"}'
```

**Upload Shapefile**

```bash
curl -X POST http://localhost:8000/v1/upload/shapefile \
  -H "Authorization: Bearer <token>" \
  -F "dataset_id=1" \
  -F "file=@flood_zones.zip"
```

**Query Features (bounding box)**

```bash
curl "http://localhost:8000/v1/features?dataset_version_id=1&bbox=-122.5,37.5,-122.0,38.0&limit=50"
```

---

## Data Model

| Table | Purpose |
|-------|---------|
| `users` | Authentication, RBAC |
| `roles` | Admin, analyst, public |
| `datasets` | Logical dataset container |
| `dataset_versions` | Versioned snapshots |
| `features` | Geometry + attributes |
| `processing_jobs` | Async job tracking |
| `audit_logs` | Immutable audit trail |

---

## Database Structure After Shapefile Upload

Here's what the database looks like when you upload a shapefile and it's processed.

### 1. `datasets` (logical container)

| Column | Description |
|--------|-------------|
| `id` | Primary key |
| `name` | e.g. "Flood Zones" |
| `slug` | e.g. "flood-zones" |
| `description` | Optional text |
| `metadata_json` | Optional JSON metadata |
| `created_by_id` | User who created it |
| `created_at`, `updated_at` | Timestamps |
| `deleted_at` | Soft delete (null if active) |

This is the top-level dataset you create before uploading.

### 2. `dataset_versions` (versioned snapshots)

| Column | Description |
|--------|-------------|
| `id` | Primary key |
| `dataset_id` | FK → datasets.id |
| `version` | Version number (1, 2, 3, …) |
| `status` | draft → ingesting → active → archived |
| `crs` | Default EPSG:4326 |
| `metadata_json` | Optional |
| `created_by_id` | User who triggered upload |
| `created_at`, `updated_at` | Timestamps |

On upload, a new version is created (or an existing draft is reused). Its status goes from `draft` → `ingesting` while the Celery task runs, then to `active` when ingestion finishes.

### 3. `features` (where shapefile geometries and attributes go)

| Column | Description |
|--------|-------------|
| `id` | Auto-increment primary key |
| `dataset_version_id` | FK → dataset_versions.id |
| `feature_id` | Original ID from the shapefile (or row index) |
| `geometry` | PostGIS geometry (SRID 4326) |
| `attributes_json` | All non-geometry attributes as JSON |
| `created_at`, `updated_at` | Timestamps |

Each shapefile row becomes one `features` row. Geometry is stored with PostGIS; attributes are stored as JSON.

From the ingestion task:

```python
for idx, row in gdf.iterrows():
    attrs = {k: str(v) if v is not None else None for k, v in row.drop("geometry").items()}
    geom_wkt = row.geometry.wkt if row.geometry else None
    if not geom_wkt:
        continue
    db.execute(
        text("""
            INSERT INTO features (dataset_version_id, feature_id, geometry, attributes_json, created_at, updated_at)
            VALUES (
                :dv_id,
                :fid,
                ST_GeomFromText(:wkt, 4326),
                :attrs,
                NOW(),
                NOW()
            )
        """),
        {
            "dv_id": dataset_version_id,
            "fid": str(idx) if "id" not in attrs else str(attrs.get("id", idx)),
            "wkt": geom_wkt,
            "attrs": json.dumps(attrs),
        },
    )
```

- `geometry` is inserted via `ST_GeomFromText(wkt, 4326)`.
- `attributes_json` holds all non-geometry columns as JSON.
- `feature_id` is the shapefile `id` if present, otherwise the row index.

### 4. `processing_jobs` (ingestion job record)

| Column | Description |
|--------|-------------|
| `id` | Primary key |
| `job_type` | `ingestion` |
| `status` | `pending` → `running` → `completed` or `failed` |
| `celery_task_id` | Celery task ID |
| `initiated_by_id` | User who uploaded |
| `parameters_json` | e.g. `{"dataset_version_id": 1, "file_path": "uploads/abc123.zip"}` |
| `result_json` | e.g. `{"features_ingested": 150}` on success |
| `error_message` | Error text if failed |
| `created_at`, `started_at`, `completed_at` | Timestamps |

### 5. `audit_logs`

Records actions such as `upload_start` with dataset version, task ID, and filename.

### Processing Flow

1. **Upload** → `.zip` saved to `uploads/`, `dataset_versions` row created/updated with `status = ingesting`, `processing_jobs` row created.
2. **Celery task** → Reads shapefile with GeoPandas, reprojects to EPSG:4326, validates/repairs geometry, bulk inserts into `features`.
3. **Completion** → `dataset_versions.status` set to `active`, `processing_jobs.status` set to `completed`, `result_json` stores feature count.

### Example `features` Row

For a shapefile with columns `id`, `name`, `zone_type`, `area_sqkm` plus geometry:

| id | dataset_version_id | feature_id | geometry | attributes_json |
|----|--------------------|------------|----------|------------------|
| 1 | 1 | 0 | `POLYGON((-122.4 37.8,...))` | `{"id": "0", "name": "Zone A", "zone_type": "100yr", "area_sqkm": "2.5"}` |

`geometry` uses PostGIS types (point, line, polygon, etc.). There is a GIST index on `geometry` for spatial queries (bbox, intersects, near).

---

## Project Structure

```
enterprise-geospatial-platform/
├── frontend/              # React + Vite + Leaflet dashboard
├── app/
│   ├── api/               # API routes
│   ├── core/              # Config, database, auth
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   ├── worker/            # Celery tasks
│   └── main.py
├── alembic/               # Database migrations
├── config/
├── scripts/
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Frontend

React + Vite + Leaflet web dashboard:

- **Login** — JWT authentication
- **Dashboard** — Dataset overview
- **Datasets** — Create and manage datasets
- **Map** — Interactive spatial query interface
- **Upload** — Shapefile ingestion UI

---

## Deployment

**Supported:**

- Docker Compose (local development)
- Production container deployments
- Kubernetes (liveness/readiness probes)
- Horizontal scaling (API + Celery workers)

**Recommended production:**

- Dedicated PostGIS instance
- PgBouncer for connection pooling
- TLS termination at load balancer
- Persistent Redis
- GeoServer heap tuning
- Prometheus monitoring

See [DEPLOYMENT.md](DEPLOYMENT.md) for details.

### Production Checklist

| Item | Description |
|------|-------------|
| **Secrets** | Set `SECRET_KEY`, DB passwords via env (never commit) |
| **TLS** | Terminate SSL at load balancer; use `X-Forwarded-*` headers |
| **Database** | Run migrations: `alembic upgrade head` before app start |
| **Health** | Configure `/health` and `/metrics-ready` for orchestration |
| **Logging** | Use structlog; ship logs to centralized aggregator |
| **Backups** | pg_dump + WAL archiving for PostGIS; test restore |

---

## Future Scope and Implementation

### Data Formats & Ingestion

- **GeoJSON / GeoPackage support** — Extend upload pipeline beyond shapefiles to accept GeoJSON, GeoPackage (.gpkg), and KML
- **Raster ingestion** — Support for GeoTIFF and other raster formats with tile generation for web maps
- **Streaming uploads** — Chunked upload for large files with progress tracking and resume capability
- **Automated sync** — Scheduled ingestion from external URLs, S3 buckets, or FTP sources

### Spatial Processing

- **Clip / intersect operations** — Crop features by polygon boundary with output dataset creation
- **Dissolve / union** — Aggregate features by attribute with geometry merging
- **Network analysis** — Shortest path, service area, and routing (e.g., pgRouting integration)
- **Raster analysis** — Zonal statistics, slope, aspect, and overlay operations
- **Change detection** — Compare dataset versions and highlight differences

### API & Integration

- **OGC API Features** — Full OGC API - Features compliance for standards-based access
- **Webhooks** — Notify external systems when ingestion or processing jobs complete
- **API versioning** — Explicit v2 with backward compatibility
- **GraphQL API** — Flexible querying for complex frontend needs
- **Bulk export** — Export datasets as shapefile, GeoJSON, or GeoPackage via async job

### Frontend & UX

- **Real-time job status** — WebSocket or SSE for live ingestion/processing progress
- **Attribute filtering** — Filter features by attribute values in the map UI
- **Style editor** — Configure layer symbology (colors, labels, popups) per dataset
- **Measurement tools** — Distance, area, and coordinate display on the map
- **Mobile-responsive** — Touch-optimized map controls and offline-capable PWA

### Security & Compliance

- **Dataset-level permissions** — Fine-grained access control per dataset or version
- **API keys** — Long-lived tokens for machine-to-machine integration
- **OAuth2 / SAML** — Enterprise SSO integration
- **Data encryption at rest** — Field-level or full-database encryption options
- **Compliance reporting** — Audit exports for SOC2, HIPAA, or agency requirements

### Scalability & Performance

- **Table partitioning** — Partition `features` by dataset or version for large deployments
- **Read replicas** — PostgreSQL read replicas for query scaling
- **Vector tiles** — Pre-generated or on-the-fly MVT for fast map rendering
- **Caching layer** — Redis caching for frequent spatial queries
- **Horizontal worker scaling** — Celery autoscaling based on queue depth

### Implementation Phases

| Phase | Focus | Timeline |
|-------|-------|----------|
| **Phase 1** | GeoJSON/GeoPackage upload, real-time job status, attribute filtering | Near-term |
| **Phase 2** | OGC API Features, webhooks, dataset-level permissions | Mid-term |
| **Phase 3** | Raster support, network analysis, vector tiles | Long-term |
| **Phase 4** | Enterprise SSO, compliance tooling, multi-tenant isolation | Future |

---

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — System design and data flows
- [DEPLOYMENT.md](DEPLOYMENT.md) — Deployment guide
- API docs: `http://localhost:8000/docs` (Swagger) or `/redoc` (ReDoc)
