"""Processing job model for async spatial operations."""

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, Index
from sqlalchemy.orm import relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class ProcessingJobStatus(str, enum.Enum):
    """Job execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingJobType(str, enum.Enum):
    """Types of processing operations."""

    INGESTION = "ingestion"
    BUFFER = "buffer"
    SPATIAL_JOIN = "spatial_join"
    RISK_SCORE = "risk_score"
    TOPOLOGY_VALIDATE = "topology_validate"


class ProcessingJob(Base):
    """Async processing job record."""

    __tablename__ = "processing_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(Enum(ProcessingJobType, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
    status = Column(Enum(ProcessingJobStatus, values_callable=lambda x: [e.value for e in x]), default=ProcessingJobStatus.PENDING, nullable=False, index=True)
    celery_task_id = Column(String(255), nullable=True, index=True)
    initiated_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    parameters_json = Column(Text, nullable=True)  # Input parameters
    result_json = Column(Text, nullable=True)  # Output/result
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_processing_jobs_status_created", "status", "created_at"),
    )
