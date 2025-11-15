"""Audit logging service."""

import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.audit import AuditLog, AuditAction


class AuditService:
    """Service for writing audit log entries."""

    def log(
        self,
        db: Session,
        action: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        user_id: Optional[int] = None,
        details: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """Create an audit log entry."""
        try:
            action_enum = AuditAction(action)
        except ValueError:
            action_enum = AuditAction.DATASET_UPDATE  # fallback

        entry = AuditLog(
            action=action_enum,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            details_json=json.dumps(details) if details else None,
            ip_address=ip_address,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry


audit_service = AuditService()
