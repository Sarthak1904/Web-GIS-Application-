# Production Deployment Guide

## Pre-Deployment Checklist

- [ ] Set strong `SECRET_KEY` (e.g. `openssl rand -hex 32`)
- [ ] Configure production `DATABASE_URL` with dedicated PostGIS instance
- [ ] Configure `REDIS_URL` and `CELERY_BROKER_URL`
- [ ] Set `APP_ENV=production` and `DEBUG=false`
- [ ] Review `MAX_UPLOAD_SIZE_MB` and `MAX_PAGE_SIZE` for your workload

## Docker Compose Production Overrides

Create `docker-compose.prod.yml`:

```yaml
version: "3.9"
services:
  backend:
    environment:
      APP_ENV: production
      DEBUG: "false"
      SECRET_KEY: ${SECRET_KEY}
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G

  celery_worker:
    deploy:
      replicas: 4
      resources:
        limits:
          memory: 2G
```

Run: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`

## Database

- Use managed PostgreSQL (e.g. AWS RDS, Azure Database) with PostGIS extension
- Enable connection pooling (PgBouncer) for high concurrency
- Schedule `VACUUM ANALYZE` on `features` table
- Monitor spatial index usage: `pg_stat_user_indexes`

## GeoServer

- Allocate sufficient JVM heap: `-Xmx4g -Xms2g` for large deployments
- Configure GeoServer clustering if serving high WMS/WFS load
- Publish layers from PostGIS datastore after ingestion

## Monitoring

- **Health**: `/health` for liveness
- **Readiness**: `/metrics-ready` (extend with DB/Redis checks)
- **Logging**: Structured JSON logs (structlog)
- **Metrics**: Add Prometheus exporter for request latency, queue depth

## Backup

- PostgreSQL: Continuous WAL archiving or daily pg_dump
- Redis: RDB snapshots or AOF
- GeoServer data_dir: Backup after layer configuration changes
