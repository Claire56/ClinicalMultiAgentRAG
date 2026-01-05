"""RAG query schemas."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ClinicalQueryRequest(BaseModel):
    """Schema for clinical query request."""
    patient_id: int = Field(..., description="Patient ID to analyze")
    query: str = Field(..., min_length=1, description="Clinical question or symptoms")
    include_history: bool = Field(True, description="Include patient history in analysis")
    urgency: str = Field("normal", description="Urgency level: low, normal, high, critical")


class AgentResponse(BaseModel):
    """Response from a single agent."""
    agent_name: str
    findings: List[str]
    recommendations: List[str]
    confidence: float = Field(..., ge=0.0, le=1.0)
    sources: List[str] = []


class CarePlanItem(BaseModel):
    """Individual care plan item."""
    action: str
    priority: str
    timeline: str
    responsible_party: Optional[str] = None


class CarePlanResponse(BaseModel):
    """Complete care plan response."""
    patient_id: int
    query: str
    summary: str
    agent_responses: List[AgentResponse]
    care_plan: List[CarePlanItem]
    risk_assessment: Dict[str, Any]
    recommended_tests: List[str]
    medication_recommendations: List[str]
    follow_up_required: bool
    follow_up_timeline: Optional[str] = None
    generated_at: datetime
    processing_time_seconds: float

