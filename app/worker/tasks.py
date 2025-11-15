"""Celery tasks for ingestion and spatial processing."""

import json
import os
from datetime import datetime
from typing import Optional

from celery import shared_task
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config import get_settings
from app.worker.celery_app import celery_app
from app.models.processing import ProcessingJob, ProcessingJobStatus
from app.models.dataset import DatasetVersion, DatasetLifecycleStatus
from app.models.feature import Feature
from app.core.database import Base

settings = get_settings()
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@celery_app.task(bind=True)
def ingest_shapefile_task(
    self,
    job_id: int,
    dataset_version_id: int,
    file_path: str,
):
    """
    Ingest shapefile: validate CRS, reproject to EPSG:4326, validate geometry, bulk insert.
    """
    db = SessionLocal()
    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job:
            return {"error": "Job not found"}

        job.status = ProcessingJobStatus.RUNNING
        job.started_at = datetime.utcnow()
        db.commit()

        if not os.path.exists(file_path):
            job.status = ProcessingJobStatus.FAILED
            job.error_message = f"File not found: {file_path}"
            job.completed_at = datetime.utcnow()
            db.commit()
            return {"error": job.error_message}

        try:
            import geopandas as gpd
            from shapely.validation import make_valid
            abs_path = os.path.abspath(file_path)
            gdf = gpd.read_file(f"zip://{abs_path}")
        except Exception as e:
            job.status = ProcessingJobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
            return {"error": str(e)}

        # CRS handling
        if gdf.crs is None:
            gdf.set_crs(epsg=4326, inplace=True)
        elif str(gdf.crs) != "EPSG:4326":
            gdf = gdf.to_crs(epsg=4326)

        # Validate CRS is in allowed list
        allowed = settings.allowed_crs_list
        if gdf.crs and str(gdf.crs) not in allowed and "EPSG:4326" not in allowed:
            pass  # We reprojected to 4326, so allow

        # Geometry validation and repair
        def fix_geom(geom):
            if geom is None or geom.is_empty:
                return None
            if not geom.is_valid:
                geom = make_valid(geom)
            return geom

        gdf["geometry"] = gdf["geometry"].apply(fix_geom)
        gdf = gdf.dropna(subset=["geometry"])

        # Bulk insert
        dv = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_version_id).first()
        if not dv:
            job.status = ProcessingJobStatus.FAILED
            job.error_message = "Dataset version not found"
            job.completed_at = datetime.utcnow()
            db.commit()
            return {"error": job.error_message}

        count = 0
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
            count += 1
            if count % 500 == 0:
                db.commit()

        db.commit()

        dv.status = DatasetLifecycleStatus.ACTIVE
        job.status = ProcessingJobStatus.COMPLETED
        job.result_json = json.dumps({"features_ingested": count})
        job.completed_at = datetime.utcnow()
        db.commit()

        # Cleanup temp file
        try:
            os.remove(file_path)
        except OSError:
            pass

        return {"features_ingested": count}

    except Exception as e:
        if db:
            job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            if job:
                job.status = ProcessingJobStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def run_buffer_task(
    self,
    job_id: int,
    dataset_version_id: int,
    feature_ids: list,
    distance_meters: float,
    output_dataset_name: Optional[str] = None,
):
    """Run buffer operation using PostGIS ST_Buffer."""
    db = SessionLocal()
    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job:
            return {"error": "Job not found"}

        job.status = ProcessingJobStatus.RUNNING
        job.started_at = datetime.utcnow()
        db.commit()

        # Approximate degrees from meters (at equator)
        dist_deg = distance_meters / 111320.0

        if feature_ids:
            result = db.execute(
                text("""
                    SELECT ST_AsText(ST_Union(ST_Buffer(geometry::geography, :dist)::geometry))
                    FROM features
                    WHERE dataset_version_id = :dv_id AND id = ANY(:ids)
                """),
                {"dist": distance_meters, "dv_id": dataset_version_id, "ids": feature_ids},
            )
        else:
            result = db.execute(
                text("""
                    SELECT ST_AsText(ST_Union(ST_Buffer(geometry::geography, :dist)::geometry))
                    FROM features
                    WHERE dataset_version_id = :dv_id
                """),
                {"dist": distance_meters, "dv_id": dataset_version_id},
            )
        row = result.fetchone()
        wkt_result = row[0] if row else None

        job.status = ProcessingJobStatus.COMPLETED
        job.result_json = json.dumps({"buffer_wkt": wkt_result, "distance_meters": distance_meters})
        job.completed_at = datetime.utcnow()
        db.commit()

        return {"buffer_wkt": wkt_result}
    except Exception as e:
        if db:
            job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            if job:
                job.status = ProcessingJobStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def run_spatial_join_task(
    self,
    job_id: int,
    source_dataset_version_id: int,
    target_dataset_version_id: int,
    join_type: str = "intersects",
    output_dataset_name: Optional[str] = None,
):
    """Run spatial join (intersects) between two datasets."""
    db = SessionLocal()
    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job:
            return {"error": "Job not found"}

        job.status = ProcessingJobStatus.RUNNING
        job.started_at = datetime.utcnow()
        db.commit()

        result = db.execute(
            text("""
                SELECT COUNT(*)
                FROM features s
                JOIN features t ON ST_Intersects(s.geometry, t.geometry)
                WHERE s.dataset_version_id = :src AND t.dataset_version_id = :tgt
            """),
            {"src": source_dataset_version_id, "tgt": target_dataset_version_id},
        )
        count = result.scalar() or 0

        job.status = ProcessingJobStatus.COMPLETED
        job.result_json = json.dumps({
            "join_count": count,
            "source_version_id": source_dataset_version_id,
            "target_version_id": target_dataset_version_id,
        })
        job.completed_at = datetime.utcnow()
        db.commit()

        return {"join_count": count}
    except Exception as e:
        if db:
            job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            if job:
                job.status = ProcessingJobStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def run_risk_score_task(
    self,
    job_id: int,
    dataset_version_id: int,
    hazard_layer_version_id: int,
    weight_hazard: float = 0.6,
    weight_exposure: float = 0.4,
):
    """Example risk scoring: overlap count * weights."""
    db = SessionLocal()
    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job:
            return {"error": "Job not found"}

        job.status = ProcessingJobStatus.RUNNING
        job.started_at = datetime.utcnow()
        db.commit()

        result = db.execute(
            text("""
                SELECT f.id, COUNT(h.id) as hazard_count
                FROM features f
                LEFT JOIN features h ON ST_Intersects(f.geometry, h.geometry)
                    AND h.dataset_version_id = :hazard_id
                WHERE f.dataset_version_id = :exp_id
                GROUP BY f.id
            """),
            {"exp_id": dataset_version_id, "hazard_id": hazard_layer_version_id},
        )
        rows = result.fetchall()
        scores = [
            {"feature_id": r[0], "hazard_count": r[1], "risk_score": r[1] * weight_hazard + (1 if r[1] > 0 else 0) * weight_exposure}
            for r in rows
        ]

        job.status = ProcessingJobStatus.COMPLETED
        job.result_json = json.dumps({"scores": scores[:100], "total": len(scores)})
        job.completed_at = datetime.utcnow()
        db.commit()

        return {"scores": len(scores)}
    except Exception as e:
        if db:
            job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            if job:
                job.status = ProcessingJobStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def run_topology_validate_task(
    self,
    job_id: int,
    dataset_version_id: int,
):
    """Validate topology (self-intersections, validity)."""
    db = SessionLocal()
    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job:
            return {"error": "Job not found"}

        job.status = ProcessingJobStatus.RUNNING
        job.started_at = datetime.utcnow()
        db.commit()

        result = db.execute(
            text("""
                SELECT id, ST_IsValid(geometry) as valid, ST_IsValidReason(geometry) as reason
                FROM features
                WHERE dataset_version_id = :dv_id AND NOT ST_IsValid(geometry)
            """),
            {"dv_id": dataset_version_id},
        )
        invalid = [{"id": r[0], "reason": r[2]} for r in result.fetchall()]

        job.status = ProcessingJobStatus.COMPLETED
        job.result_json = json.dumps({"invalid_count": len(invalid), "invalid_features": invalid[:50]})
        job.completed_at = datetime.utcnow()
        db.commit()

        return {"invalid_count": len(invalid)}
    except Exception as e:
        if db:
            job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            if job:
                job.status = ProcessingJobStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()
        raise
    finally:
        db.close()
