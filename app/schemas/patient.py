"""Patient schemas."""
from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import Optional
from app.models.patient import Gender, BloodType


class PatientBase(BaseModel):
    """Base patient schema."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    gender: Gender
    blood_type: Optional[BloodType] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    medical_history_summary: Optional[str] = None
    allergies: Optional[str] = None
    current_medications: Optional[str] = None


class PatientCreate(PatientBase):
    """Schema for creating a patient."""
    pass


class PatientUpdate(BaseModel):
    """Schema for updating a patient."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    medical_history_summary: Optional[str] = None
    allergies: Optional[str] = None
    current_medications: Optional[str] = None


class PatientResponse(PatientBase):
    """Schema for patient response."""
    id: int
    created_at: str
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True

