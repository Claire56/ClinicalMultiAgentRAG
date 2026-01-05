"""API v1 router."""
from fastapi import APIRouter
from app.api.v1.endpoints import patients, medical_records, treatments, medications, rag, auth

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patients"])
api_router.include_router(medical_records.router, prefix="/medical-records", tags=["Medical Records"])
api_router.include_router(treatments.router, prefix="/treatments", tags=["Treatments"])
api_router.include_router(medications.router, prefix="/medications", tags=["Medications"])
api_router.include_router(rag.router, prefix="/rag", tags=["RAG - Clinical Decision Support"])

