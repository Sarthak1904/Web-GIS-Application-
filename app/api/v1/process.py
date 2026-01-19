"""Spatial processing endpoints — buffer, spatial join, risk score, topology."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.processing import ProcessingJob, ProcessingJobType, ProcessingJobStatus
from app.api.deps import require_role
from pydantic import BaseModel
from app.schemas.feature import BufferRequest, SpatialJoinRequest, RiskScoreRequest
from app.services.audit import audit_service
from app.worker.tasks import run_buffer_task, run_spatial_join_task, run_risk_score_task, run_topology_validate_task

router = APIRouter(prefix="/process", tags=["process"])


@router.post("/buffer")
def create_buffer_job(
    payload: BufferRequest,
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(require_role("admin", "analyst"))] = None,
):
    """Enqueue buffer processing job."""
    job = ProcessingJob(
        job_type=ProcessingJobType.BUFFER,
        status=ProcessingJobStatus.PENDING,
        initiated_by_id=current_user.id,
        parameters_json=payload.model_dump_json(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    task = run_buffer_task.delay(
        job_id=job.id,
        dataset_version_id=payload.dataset_version_id,
        feature_ids=payload.feature_ids,
        distance_meters=payload.distance_meters,
        output_dataset_name=payload.output_dataset_name,
    )
    job.celery_task_id = task.id
    db.commit()

    audit_service.log(
        db=db,
        action="processing_start",
        entity_type="processing_job",
        entity_id=str(job.id),
        user_id=current_user.id,
        details={"job_type": "buffer", "task_id": task.id},
    )

    return {"job_id": job.id, "task_id": task.id, "status": "pending"}


@router.post("/spatial-join")
def create_spatial_join_job(
    payload: SpatialJoinRequest,
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(require_role("admin", "analyst"))] = None,
):
    """Enqueue spatial join processing job."""
    job = ProcessingJob(
        job_type=ProcessingJobType.SPATIAL_JOIN,
        status=ProcessingJobStatus.PENDING,
        initiated_by_id=current_user.id,
        parameters_json=payload.model_dump_json(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    task = run_spatial_join_task.delay(
        job_id=job.id,
        source_dataset_version_id=payload.source_dataset_version_id,
        target_dataset_version_id=payload.target_dataset_version_id,
        join_type=payload.join_type,
        output_dataset_name=payload.output_dataset_name,
    )
    job.celery_task_id = task.id
    db.commit()

    audit_service.log(
        db=db,
        action="processing_start",
        entity_type="processing_job",
        entity_id=str(job.id),
        user_id=current_user.id,
        details={"job_type": "spatial_join", "task_id": task.id},
    )

    return {"job_id": job.id, "task_id": task.id, "status": "pending"}


@router.post("/risk-score")
def create_risk_score_job(
    payload: RiskScoreRequest,
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(require_role("admin", "analyst"))] = None,
):
    """Enqueue risk scoring job (example)."""
    job = ProcessingJob(
        job_type=ProcessingJobType.RISK_SCORE,
        status=ProcessingJobStatus.PENDING,
        initiated_by_id=current_user.id,
        parameters_json=payload.model_dump_json(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    task = run_risk_score_task.delay(
        job_id=job.id,
        dataset_version_id=payload.dataset_version_id,
        hazard_layer_version_id=payload.hazard_layer_version_id,
        weight_hazard=payload.weight_hazard,
        weight_exposure=payload.weight_exposure,
    )
    job.celery_task_id = task.id
    db.commit()

    audit_service.log(
        db=db,
        action="processing_start",
        entity_type="processing_job",
        entity_id=str(job.id),
        user_id=current_user.id,
        details={"job_type": "risk_score", "task_id": task.id},
    )

    return {"job_id": job.id, "task_id": task.id, "status": "pending"}


class TopologyValidateRequest(BaseModel):
    """Topology validation request."""

    dataset_version_id: int


@router.post("/topology-validate")
def create_topology_validate_job(
    payload: TopologyValidateRequest,
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(require_role("admin", "analyst"))] = None,
):
    """Enqueue topology validation job."""
    dataset_version_id = payload.dataset_version_id
    job = ProcessingJob(
        job_type=ProcessingJobType.TOPOLOGY_VALIDATE,
        status=ProcessingJobStatus.PENDING,
        initiated_by_id=current_user.id,
        parameters_json=payload.model_dump_json(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    task = run_topology_validate_task.delay(job_id=job.id, dataset_version_id=dataset_version_id)
    job.celery_task_id = task.id
    db.commit()

    audit_service.log(
        db=db,
        action="processing_start",
        entity_type="processing_job",
        entity_id=str(job.id),
        user_id=current_user.id,
        details={"job_type": "topology_validate", "task_id": task.id},
    )

    return {"job_id": job.id, "task_id": task.id, "status": "pending"}


@router.get("/jobs/{job_id}")
def get_job_status(
    job_id: int,
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(require_role("admin", "analyst"))] = None,
):
    """Get processing job status and result."""
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id,
        "job_type": job.job_type.value,
        "status": job.status.value,
        "task_id": job.celery_task_id,
        "result": job.result_json,
        "error": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }
