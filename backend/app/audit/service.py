import json
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.models import AuditLog
from app.audit.schemas import AuditLogCreate


def create_audit_log(
    db: Session,
    payload: AuditLogCreate,
):
    metadata = payload.metadata_json

    try:
        json.loads(metadata)
    except (TypeError, ValueError):
        raise ValueError("Invalid audit metadata JSON")

    log = AuditLog(
        organization_id=payload.organization_id,
        user_id=payload.user_id,
        action=payload.action.strip(),
        entity_type=payload.entity_type.strip(),
        entity_id=payload.entity_id,
        description=payload.description.strip(),
        metadata_json=metadata,
    )

    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def list_audit_logs(
    db: Session,
    organization_id: uuid.UUID,
    limit: int = 100,
):
    return list(
        db.scalars(
            select(AuditLog).where(
                AuditLog.organization_id == organization_id
            ).order_by(
                AuditLog.created_at.desc()
            ).limit(limit)
        ).all()
    )
