"""Database models."""
from app.models.patient import Patient
from app.models.medical_record import MedicalRecord
from app.models.treatment import Treatment
from app.models.medication import Medication
from app.models.user import User

__all__ = [
    "Patient",
    "MedicalRecord",
    "Treatment",
    "Medication",
    "User",
]

