"""Medical record schemas."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.medical_record import RecordType


class MedicalRecordBase(BaseModel):
    """Base medical record schema."""
    record_type: RecordType
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    symptoms: Optional[str] = None
    diagnosis: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None
    physician_name: str = Field(..., min_length=1, max_length=200)
    date_of_visit: datetime


class MedicalRecordCreate(MedicalRecordBase):
    """Schema for creating a medical record."""
    patient_id: int


class MedicalRecordResponse(MedicalRecordBase):
    """Schema for medical record response."""
    id: int
    patient_id: int
    created_at: str
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True

