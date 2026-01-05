"""Medication model."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class MedicationStatus(str, enum.Enum):
    """Medication status."""
    ACTIVE = "active"
    DISCONTINUED = "discontinued"
    COMPLETED = "completed"


class Medication(Base):
    """Medication model."""
    __tablename__ = "medications"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    medication_name = Column(String(255), nullable=False)
    dosage = Column(String(100), nullable=False)
    frequency = Column(String(100), nullable=False)
    route = Column(String(50), nullable=False)  # oral, IV, topical, etc.
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(MedicationStatus), nullable=False, default=MedicationStatus.ACTIVE)
    prescribing_physician = Column(String(200), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="medications")

