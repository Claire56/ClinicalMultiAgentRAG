"""Medical record model."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class RecordType(str, enum.Enum):
    """Medical record type."""
    CONSULTATION = "consultation"
    LAB_RESULT = "lab_result"
    IMAGING = "imaging"
    PROCEDURE = "procedure"
    DIAGNOSIS = "diagnosis"
    NOTE = "note"


class MedicalRecord(Base):
    """Medical record model."""
    __tablename__ = "medical_records"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    record_type = Column(Enum(RecordType), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    symptoms = Column(Text, nullable=True)
    diagnosis = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    physician_name = Column(String(200), nullable=False)
    date_of_visit = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    patient = relationship("Patient", back_populates="medical_records")

