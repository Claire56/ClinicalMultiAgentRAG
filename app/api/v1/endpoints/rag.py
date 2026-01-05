"""RAG endpoints for clinical decision support."""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user, get_user_by_api_key
from app.core.config import settings
from app.models.user import User
from app.schemas.rag import ClinicalQueryRequest, ClinicalQueryResponse, CarePlanResponse
from app.services.rag_service import RAGService
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter()
rag_service = RAGService()


async def get_authenticated_user(
    authorization: Optional[str] = Header(None),
    api_key: Optional[str] = Header(None, alias=settings.API_KEY_HEADER_NAME),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get authenticated user via JWT or API key."""
    if api_key:
        user = await get_user_by_api_key(api_key, db)
        if user:
            return user
    
    if authorization:
        # This would use get_current_user, simplified for demo
        pass
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
    )


@router.post("/clinical-query", response_model=ClinicalQueryResponse)
async def clinical_query(
    request: ClinicalQueryRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_authenticated_user),
):
    """
    Process a clinical query using agentic RAG.
    
    This endpoint uses multiple AI agents to analyze patient data and provide
    evidence-based clinical recommendations.
    """
    try:
        logger.info(
            "Processing clinical query",
            patient_id=request.patient_id,
            query=request.query,
            user_id=user.id,
        )
        
        # Process query with RAG service
        result = await rag_service.process_clinical_query(
            db=db,
            patient_id=request.patient_id,
            query=request.query,
            include_history=request.include_history,
        )
        
        # Build response
        response = ClinicalQueryResponse(
            patient_id=request.patient_id,
            query=request.query,
            summary=result["summary"],
            agent_responses=result["agent_responses"],
            care_plan=result["care_plan"],
            risk_assessment=result["risk_assessment"],
            recommended_tests=result["recommended_tests"],
            medication_recommendations=result["medication_recommendations"],
            follow_up_required=len(result["care_plan"]) > 0,
            follow_up_timeline="Within 24-48 hours" if request.urgency in ["high", "critical"] else "Within 1 week",
            generated_at=datetime.utcnow(),
            processing_time_seconds=result["processing_time_seconds"],
        )
        
        logger.info(
            "Clinical query completed",
            patient_id=request.patient_id,
            processing_time=result["processing_time_seconds"],
        )
        
        return response
        
    except ValueError as e:
        logger.error("Clinical query failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Clinical query error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process clinical query",
        )


@router.get("/care-plan/{patient_id}", response_model=CarePlanResponse)
async def get_care_plan(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_authenticated_user),
):
    """Get care plan for a patient."""
    # This would retrieve a saved care plan
    # For now, return a placeholder
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Care plan retrieval not yet implemented",
    )

