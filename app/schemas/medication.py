"""Medication schemas."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.medication import MedicationStatus


class MedicationBase(BaseModel):
    """Base medication schema."""
    medication_name: str = Field(..., min_length=1, max_length=255)
    dosage: str = Field(..., min_length=1, max_length=100)
    frequency: str = Field(..., min_length=1, max_length=100)
    route: str = Field(..., min_length=1, max_length=50)
    start_date: datetime
    end_date: Optional[datetime] = None
    status: MedicationStatus = MedicationStatus.ACTIVE
    prescribing_physician: str = Field(..., min_length=1, max_length=200)
    notes: Optional[str] = None


class MedicationCreate(MedicationBase):
    """Schema for creating a medication."""
    patient_id: int


class MedicationResponse(MedicationBase):
    """Schema for medication response."""
    id: int
    patient_id: int
    created_at: str
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True

