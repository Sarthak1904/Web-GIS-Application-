"""Dataset upload and ingestion endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.dataset import Dataset, DatasetVersion, DatasetLifecycleStatus
from app.models.processing import ProcessingJob, ProcessingJobType, ProcessingJobStatus
from app.models.user import User
from app.api.deps import get_current_user, require_role
from app.services.audit import audit_service
from app.worker.tasks import ingest_shapefile_task
from config import get_settings

router = APIRouter(prefix="/upload", tags=["upload"])

settings = get_settings()


@router.post("/shapefile")
async def upload_shapefile(
    dataset_id: Annotated[int, Form()],
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(require_role("admin", "analyst"))] = None,
):
    """
    Upload a shapefile (.zip) for ingestion.
    Validates CRS, reprojects to EPSG:4326, validates geometry, bulk inserts.
    Runs as async background job.
    """
    ds = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.deleted_at.is_(None)).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip shapefile bundles are accepted")

    # Read file content (limit size)
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    content = b""
    size = 0
    while chunk := await file.read(8192):
        content += chunk
        size += len(chunk)
        if size > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds max size of {settings.max_upload_size_mb}MB",
            )

    # Save to temp location for Celery worker
    import os
    import uuid
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    temp_path = os.path.join(upload_dir, f"{uuid.uuid4().hex}.zip")
    with open(temp_path, "wb") as f:
        f.write(content)

    # Create new version or use existing draft
    versions = [v for v in ds.versions if v.deleted_at is None]
    draft = next((v for v in versions if v.status == DatasetLifecycleStatus.DRAFT), None)
    if draft:
        dv = draft
        dv.status = DatasetLifecycleStatus.INGESTING
    else:
        next_ver = max((v.version for v in versions), default=0) + 1
        dv = DatasetVersion(
            dataset_id=ds.id,
            version=next_ver,
            status=DatasetLifecycleStatus.INGESTING,
            crs=settings.default_crs,
            created_by_id=current_user.id,
        )
        db.add(dv)
    db.commit()
    db.refresh(dv)

    # Create processing job
    job = ProcessingJob(
        job_type=ProcessingJobType.INGESTION,
        status=ProcessingJobStatus.PENDING,
        initiated_by_id=current_user.id,
        parameters_json=f'{{"dataset_version_id": {dv.id}, "file_path": "{temp_path}"}}',
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Enqueue Celery task
    task = ingest_shapefile_task.delay(
        job_id=job.id,
        dataset_version_id=dv.id,
        file_path=temp_path,
    )
    job.celery_task_id = task.id
    db.commit()

    audit_service.log(
        db=db,
        action="upload_start",
        entity_type="dataset_version",
        entity_id=str(dv.id),
        user_id=current_user.id,
        details={"dataset_id": dataset_id, "task_id": task.id, "filename": file.filename},
    )

    return {
        "job_id": job.id,
        "task_id": task.id,
        "dataset_version_id": dv.id,
        "status": "pending",
        "message": "Ingestion job queued. Poll /v1/process/jobs/{job_id} for status.",
    }
