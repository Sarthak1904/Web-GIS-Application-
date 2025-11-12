"""Dataset management endpoints."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.dataset import Dataset, DatasetVersion, DatasetLifecycleStatus
from app.models.user import User
from app.api.deps import get_current_user, require_role
from app.schemas.dataset import DatasetCreate, DatasetResponse, DatasetVersionResponse
from app.services.audit import audit_service

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=DatasetResponse)
def create_dataset(
    payload: DatasetCreate,
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(require_role("admin", "analyst"))] = None,
):
    """Create a new dataset (admin/analyst)."""
    existing = db.query(Dataset).filter(Dataset.slug == payload.slug, Dataset.deleted_at.is_(None)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Dataset slug already exists")

    ds = Dataset(
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        metadata_json=payload.metadata_json,
        created_by_id=current_user.id,
    )
    db.add(ds)
    db.commit()
    db.refresh(ds)

    # Create initial version
    dv = DatasetVersion(
        dataset_id=ds.id,
        version=1,
        status=DatasetLifecycleStatus.DRAFT,
        crs="EPSG:4326",
        created_by_id=current_user.id,
    )
    db.add(dv)
    db.commit()

    audit_service.log(
        db=db,
        action="dataset_create",
        entity_type="dataset",
        entity_id=str(ds.id),
        user_id=current_user.id,
        details={"name": ds.name, "slug": ds.slug},
    )

    return ds


@router.get("", response_model=list[DatasetResponse])
def list_datasets(
    include_deleted: bool = Query(False),
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(require_role("admin", "analyst", "public"))] = None,
):
    """List datasets. Public role sees only active datasets."""
    q = db.query(Dataset)
    if not include_deleted:
        q = q.filter(Dataset.deleted_at.is_(None))
    return q.order_by(Dataset.name).all()


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(
    dataset_id: int,
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(require_role("admin", "analyst", "public"))] = None,
):
    """Get dataset by ID."""
    ds = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.deleted_at.is_(None)).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return ds


@router.delete("/{dataset_id}")
@router.post("/{dataset_id}/delete")
def delete_dataset(
    dataset_id: int,
    permanent: bool = Query(False, description="If true, permanently remove from database. Otherwise soft-delete."),
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(require_role("admin", "analyst"))] = None,
):
    """Delete a dataset. Use permanent=true to remove from database entirely (admin/analyst)."""
    q = db.query(Dataset).filter(Dataset.id == dataset_id)
    if not permanent:
        q = q.filter(Dataset.deleted_at.is_(None))
    ds = q.first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

    name, slug = ds.name, ds.slug

    if permanent:
        # Hard delete: remove versions (cascades to features), then dataset
        for dv in db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id).all():
            db.delete(dv)
        db.delete(ds)
        db.commit()
        msg = "Dataset permanently deleted"
    else:
        ds.deleted_at = datetime.utcnow()
        db.commit()
        msg = "Dataset deleted (soft). Use ?permanent=true to remove from database."

    audit_service.log(
        db=db,
        action="dataset_delete",
        entity_type="dataset",
        entity_id=str(dataset_id),
        user_id=current_user.id,
        details={"name": name, "slug": slug, "permanent": permanent},
    )

    return {"message": msg}


@router.post("/{dataset_id}/versions/{version_id}/reset-ingestion")
def reset_stuck_ingestion(
    dataset_id: int,
    version_id: int,
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(require_role("admin", "analyst"))] = None,
):
    """Reset a version stuck in 'ingesting' back to 'draft' so it can be re-uploaded."""
    dv = db.query(DatasetVersion).filter(
        DatasetVersion.id == version_id,
        DatasetVersion.dataset_id == dataset_id,
        DatasetVersion.deleted_at.is_(None),
    ).first()
    if not dv:
        raise HTTPException(status_code=404, detail="Version not found")
    if dv.status != DatasetLifecycleStatus.INGESTING:
        raise HTTPException(status_code=400, detail="Only ingesting versions can be reset")
    dv.status = DatasetLifecycleStatus.DRAFT
    db.commit()
    return {"message": "Reset to draft. Re-upload the shapefile."}


@router.get("/{dataset_id}/versions", response_model=list[DatasetVersionResponse])
def list_versions(
    dataset_id: int,
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(require_role("admin", "analyst", "public"))] = None,
):
    """List versions for a dataset."""
    ds = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.deleted_at.is_(None)).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return ds.versions
