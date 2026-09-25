import uuid

from pydantic import BaseModel, Field


class AuditLogCreate(BaseModel):
    organization_id: uuid.UUID
    user_id: uuid.UUID | None = None
    action: str = Field(
        min_length=1,
        max_length=100,
    )
    entity_type: str = Field(
        min_length=1,
        max_length=100,
    )
    entity_id: uuid.UUID | None = None
    description: str = ""
    metadata_json: str = "{}"


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: uuid.UUID | None
    description: str
    metadata_json: str
    created_at: object
