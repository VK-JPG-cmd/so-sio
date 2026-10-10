from datetime import datetime
import uuid
from pydantic import BaseModel, ConfigDict
from app.models.enums import EvidenceType


class EvidenceResponse(BaseModel):
    """Metadata response for a secure threat evidence attachment."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    report_id: uuid.UUID
    evidence_type: EvidenceType
    storage_key: str
    sha256: str
    original_filename: str
    file_size: int
    created_at: datetime
