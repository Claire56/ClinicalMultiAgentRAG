"""Treatment schemas."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.treatment import TreatmentStatus


class TreatmentBase(BaseModel):
    """Base treatment schema."""
    treatment_name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    status: TreatmentStatus = TreatmentStatus.PLANNED
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    physician_name: str = Field(..., min_length=1, max_length=200)
    notes: Optional[str] = None


class TreatmentCreate(TreatmentBase):
    """Schema for creating a treatment."""
    patient_id: int


class TreatmentResponse(TreatmentBase):
    """Schema for treatment response."""
    id: int
    patient_id: int
    created_at: str
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True

