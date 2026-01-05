"""Treatment endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.models.treatment import Treatment
from app.schemas.treatment import TreatmentCreate, TreatmentResponse
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=TreatmentResponse, status_code=status.HTTP_201_CREATED)
async def create_treatment(
    treatment: TreatmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "physician"])),
):
    """Create a new treatment."""
    db_treatment = Treatment(**treatment.model_dump())
    db.add(db_treatment)
    await db.commit()
    await db.refresh(db_treatment)
    
    logger.info("Treatment created", treatment_id=db_treatment.id, user_id=current_user.id)
    return db_treatment


@router.get("/patient/{patient_id}", response_model=List[TreatmentResponse])
async def get_patient_treatments(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get treatments for a patient."""
    result = await db.execute(
        select(Treatment)
        .where(Treatment.patient_id == patient_id)
        .order_by(Treatment.start_date.desc())
    )
    treatments = result.scalars().all()
    return treatments

