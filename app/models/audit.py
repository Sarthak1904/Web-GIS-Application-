"""Audit log for tracking dataset and system changes."""

import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class AuditAction(str, enum.Enum):
    """Audit event types."""

    DATASET_CREATE = "dataset_create"
    DATASET_UPDATE = "dataset_update"
    DATASET_DELETE = "dataset_delete"
    VERSION_CREATE = "version_create"
    VERSION_UPDATE = "version_update"
    UPLOAD_START = "upload_start"
    UPLOAD_COMPLETE = "upload_complete"
    UPLOAD_FAILED = "upload_failed"
    PROCESSING_START = "processing_start"
    PROCESSING_COMPLETE = "processing_complete"
    PROCESSING_FAILED = "processing_failed"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"


class AuditLog(Base):
    """Immutable audit log entry."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(Enum(AuditAction, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
    entity_type = Column(String(100), nullable=True, index=True)  # dataset, feature, user, etc.
    entity_id = Column(String(100), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    details_json = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_audit_logs_created", "created_at"),
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
    )
