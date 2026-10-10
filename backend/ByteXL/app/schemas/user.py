from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import AccountStatus, UserRole


class UserProfileResponse(BaseModel):
    """Safe user profile response representation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Unique user identifier")
    phone_number: str = Field(..., description="Normalized E.164 phone number")
    phone_verified_at: Optional[datetime] = Field(
        default=None, description="Timestamp when phone number was verified"
    )
    role: UserRole = Field(..., description="User role in the system")
    account_status: AccountStatus = Field(..., description="Current status of the account")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Account last update timestamp")
