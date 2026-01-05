"""Medication endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.models.medication import Medication
from app.schemas.medication import MedicationCreate, MedicationResponse
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=MedicationResponse, status_code=status.HTTP_201_CREATED)
async def create_medication(
    medication: MedicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "physician"])),
):
    """Create a new medication record."""
    db_medication = Medication(**medication.model_dump())
    db.add(db_medication)
    await db.commit()
    await db.refresh(db_medication)
    
    logger.info("Medication created", medication_id=db_medication.id, user_id=current_user.id)
    return db_medication


@router.get("/patient/{patient_id}", response_model=List[MedicationResponse])
async def get_patient_medications(
    patient_id: int,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get medications for a patient."""
    query = select(Medication).where(Medication.patient_id == patient_id)
    
    if active_only:
        from app.models.medication import MedicationStatus
        query = query.where(Medication.status == MedicationStatus.ACTIVE)
    
    result = await db.execute(query.order_by(Medication.start_date.desc()))
    medications = result.scalars().all()
    return medications

