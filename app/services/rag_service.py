"""RAG service for clinical decision support."""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from app.models.patient import Patient
from app.models.medical_record import MedicalRecord
from app.models.medication import Medication
from app.models.treatment import Treatment
from app.schemas.rag import AgentResponse, CarePlanItem
from app.services.pinecone_service import PineconeService
from app.services.tavily_service import TavilyService
import structlog
import time

logger = structlog.get_logger(__name__)


class RAGService:
    """Service for agentic RAG operations."""
    
    def __init__(self):
        """Initialize RAG service."""
        self.pinecone_service = PineconeService()
        self.tavily_service = TavilyService()
        self.llm = None
        
        # Initialize LLM if available
        try:
            self.llm = self.pinecone_service.get_llm(temperature=0.0)
        except Exception as e:
            logger.warning("LLM not initialized", error=str(e))
    
    async def get_patient_context(
        self,
        db: AsyncSession,
        patient_id: int,
    ) -> Dict[str, Any]:
        """Retrieve comprehensive patient context."""
        # Get patient
        result = await db.execute(select(Patient).where(Patient.id == patient_id))
        patient = result.scalar_one_or_none()
        
        if not patient:
            raise ValueError(f"Patient {patient_id} not found")
        
        # Get medical records
        records_result = await db.execute(
            select(MedicalRecord)
            .where(MedicalRecord.patient_id == patient_id)
            .order_by(MedicalRecord.date_of_visit.desc())
            .limit(10)
        )
        records = records_result.scalars().all()
        
        # Get medications
        meds_result = await db.execute(
            select(Medication)
            .where(Medication.patient_id == patient_id, Medication.status == "active")
        )
        medications = meds_result.scalars().all()
        
        # Get treatments
        treatments_result = await db.execute(
            select(Treatment)
            .where(Treatment.patient_id == patient_id)
            .order_by(Treatment.start_date.desc())
            .limit(5)
        )
        treatments = treatments_result.scalars().all()
        
        return {
            "patient": patient,
            "medical_records": records,
            "medications": medications,
            "treatments": treatments,
        }
    
    async def clinical_research_agent(
        self,
        query: str,
        patient_context: Dict[str, Any],
    ) -> AgentResponse:
        """Agent that retrieves relevant medical literature and guidelines."""
        findings = []
        recommendations = []
        sources = []
        
        # Build enhanced query with patient context
        enhanced_query = f"{query}. Patient context: "
        if patient_context.get("patient"):
            patient = patient_context["patient"]
            enhanced_query += f"Age: {self._calculate_age(patient.date_of_birth)}, "
            if patient.medical_history_summary:
                enhanced_query += f"History: {patient.medical_history_summary[:200]}, "
        
        # Hybrid search: Pinecone (static knowledge) + Tavily (real-time web search)
        all_documents = []
        
        # 1. Search Pinecone for established guidelines
        if self.pinecone_service.vector_store:
            try:
                pinecone_results = await self.pinecone_service.similarity_search(
                    enhanced_query,
                    k=5,
                    namespace="medical_guidelines",
                )
                all_documents.extend(pinecone_results)
                logger.info("Pinecone search completed", results=len(pinecone_results))
            except Exception as e:
                logger.error("Pinecone search error", error=str(e))
        
        # 2. Search Tavily for latest research and guidelines
        if self.tavily_service.tavily_tool:
            try:
                # Search for latest medical literature
                tavily_results = await self.tavily_service.search_medical_literature(
                    query=query,
                    max_results=3,
                )
                all_documents.extend(tavily_results)
                logger.info("Tavily search completed", results=len(tavily_results))
                
                # Also search for latest guidelines if query mentions a condition
                if any(keyword in query.lower() for keyword in ["treatment", "guideline", "protocol", "management"]):
                    condition_keywords = ["diabetes", "hypertension", "chest pain", "heart", "cardiac"]
                    for keyword in condition_keywords:
                        if keyword in query.lower():
                            guideline_results = await self.tavily_service.search_latest_guidelines(
                                condition=keyword,
                                max_results=2,
                            )
                            all_documents.extend(guideline_results)
                            break
            except Exception as e:
                logger.error("Tavily search error", error=str(e))
        
        # Extract findings from all sources
        for doc in all_documents[:8]:  # Limit to top 8 results
            findings.append(doc.page_content[:200])
            if hasattr(doc, 'metadata'):
                source = doc.metadata.get('source', doc.metadata.get('url', 'Unknown'))
                sources.append(source)
        
        # Use LLM to synthesize findings and generate recommendations
        if self.llm and all_documents:
            try:
                context_text = "\n".join([doc.page_content for doc in all_documents[:5]])
                prompt = ChatPromptTemplate.from_messages([
                    ("system", "You are a clinical research assistant. Synthesize the medical information provided (from both established guidelines and latest research) to generate evidence-based clinical recommendations. Prioritize recent research when available."),
                    ("human", "Clinical Query: {query}\n\nPatient Context: {patient_context}\n\nMedical Information:\n{context}\n\nGenerate 3-5 specific, evidence-based clinical recommendations. Include citations when possible."),
                ])
                from langchain.chains import LLMChain
                chain = LLMChain(llm=self.llm, prompt=prompt)
                
                patient_summary = ""
                if patient_context.get("patient"):
                    patient = patient_context["patient"]
                    patient_summary = f"Age: {self._calculate_age(patient.date_of_birth)}"
                    if patient.medical_history_summary:
                        patient_summary += f", History: {patient.medical_history_summary[:150]}"
                
                result = await chain.ainvoke({
                    "query": query,
                    "patient_context": patient_summary,
                    "context": context_text,
                })
                # Extract recommendations from LLM response
                llm_recommendations = result.get("text", "").split("\n")
                recommendations.extend([r.strip() for r in llm_recommendations if r.strip() and r.strip().startswith(("-", "•", "1.", "2."))][:5])
            except Exception as e:
                logger.error("LLM recommendation generation error", error=str(e))
        
        # Fallback if no results
        if not findings:
            findings = ["No relevant guidelines found in knowledge base or web search"]
            recommendations = ["Consult standard medical protocols", "Review patient-specific factors", "Consider latest medical literature"]
            sources = ["Knowledge Base"]
        
        # Calculate confidence based on number of sources
        confidence = min(0.95, 0.6 + (len(all_documents) * 0.05))
        
        return AgentResponse(
            agent_name="Clinical Research Agent",
            findings=findings[:5],
            recommendations=recommendations[:5] if recommendations else ["Review medical literature", "Consult latest guidelines"],
            confidence=confidence,
            sources=list(set(sources[:5])) if sources else ["Clinical Guidelines Database"],
        )
    
    def _calculate_age(self, date_of_birth):
        """Calculate age from date of birth."""
        from datetime import date
        return (date.today() - date_of_birth).days // 365
    
    async def patient_history_agent(
        self,
        query: str,
        patient_context: Dict[str, Any],
    ) -> AgentResponse:
        """Agent that analyzes patient history."""
        patient = patient_context["patient"]
        records = patient_context["medical_records"]
        medications = patient_context["medications"]
        
        findings = []
        recommendations = []
        
        # Analyze allergies
        if patient.allergies:
            findings.append(f"Known allergies: {patient.allergies}")
            recommendations.append("Verify no drug interactions with current medications")
        
        # Analyze medications
        if medications:
            med_names = [m.medication_name for m in medications]
            findings.append(f"Current medications: {', '.join(med_names)}")
            recommendations.append("Review for potential interactions with new treatments")
        
        # Analyze recent records
        if records:
            recent_diagnoses = [r.diagnosis for r in records[:3] if r.diagnosis]
            if recent_diagnoses:
                findings.append(f"Recent diagnoses: {', '.join(recent_diagnoses)}")
        
        return AgentResponse(
            agent_name="Patient History Agent",
            findings=findings[:5],
            recommendations=recommendations[:5],
            confidence=0.90,
            sources=["Patient Medical Records"],
        )
    
    async def treatment_protocol_agent(
        self,
        query: str,
        patient_context: Dict[str, Any],
    ) -> AgentResponse:
        """Agent that validates treatments against protocols."""
        findings = []
        recommendations = []
        sources = []
        
        # Search for treatment protocols
        protocol_query = f"Treatment protocol for: {query}"
        if self.pinecone_service.vector_store:
            try:
                search_results = await self.pinecone_service.similarity_search(
                    protocol_query,
                    k=3,
                    namespace="treatment_protocols",
                )
                
                for doc in search_results:
                    findings.append(doc.page_content[:200])
                    if hasattr(doc, 'metadata') and 'source' in doc.metadata:
                        sources.append(doc.metadata['source'])
                
                # Use LLM to extract protocol steps
                if self.llm and search_results:
                    context_text = "\n".join([doc.page_content for doc in search_results])
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", "You are a protocol validation assistant. Extract specific protocol steps and requirements."),
                        ("human", "Query: {query}\n\nProtocols:\n{context}\n\nList the specific protocol steps and requirements."),
                    ])
                    from langchain.chains import LLMChain
                    chain = LLMChain(llm=self.llm, prompt=prompt)
                    result = await chain.ainvoke({
                        "query": query,
                        "context": context_text,
                    })
                    # Extract recommendations from LLM response
                    llm_recommendations = result.get("text", "").split("\n")
                    recommendations.extend([r.strip() for r in llm_recommendations if r.strip()][:5])
            except Exception as e:
                logger.error("Treatment protocol agent error", error=str(e))
        
        # Fallback
        if not findings:
            query_lower = query.lower()
            if "chest pain" in query_lower:
                findings.append("Chest pain protocol requires: ECG, troponin, CXR")
                recommendations.append("Follow institutional chest pain protocol")
                recommendations.append("Consider stress test if initial workup negative")
        
        return AgentResponse(
            agent_name="Treatment Protocol Agent",
            findings=findings[:5] if findings else ["Review standard protocols"],
            recommendations=recommendations[:5] if recommendations else ["Follow institutional guidelines"],
            confidence=0.88 if findings else 0.6,
            sources=sources[:3] if sources else ["Institutional Protocols"],
        )
    
    async def risk_assessment_agent(
        self,
        query: str,
        patient_context: Dict[str, Any],
    ) -> AgentResponse:
        """Agent that assesses patient risk."""
        patient = patient_context["patient"]
        findings = []
        recommendations = []
        
        # Calculate age
        age = self._calculate_age(patient.date_of_birth)
        
        if age > 65:
            findings.append("Patient is over 65 - increased risk for complications")
            recommendations.append("Consider more conservative treatment approach")
        
        if patient.medical_history_summary and "diabetes" in patient.medical_history_summary.lower():
            findings.append("Diabetes increases cardiovascular risk")
            recommendations.append("Monitor blood glucose closely during treatment")
        
        return AgentResponse(
            agent_name="Risk Assessment Agent",
            findings=findings[:5],
            recommendations=recommendations[:5],
            confidence=0.82,
            sources=["Risk Stratification Models"],
        )
    
    async def generate_care_plan(
        self,
        query: str,
        patient_id: int,
        agent_responses: List[AgentResponse],
    ) -> List[CarePlanItem]:
        """Generate care plan from agent responses."""
        care_plan = []
        
        # Extract recommendations from all agents
        all_recommendations = []
        for agent in agent_responses:
            all_recommendations.extend(agent.recommendations)
        
        # Create care plan items
        priorities = ["high", "medium", "low"]
        for i, rec in enumerate(all_recommendations[:10]):
            care_plan.append(CarePlanItem(
                action=rec,
                priority=priorities[i % 3],
                timeline="Immediate" if "immediate" in rec.lower() else "Within 24-48 hours",
                responsible_party="Primary Physician",
            ))
        
        return care_plan
    
    async def process_clinical_query(
        self,
        db: AsyncSession,
        patient_id: int,
        query: str,
        include_history: bool = True,
    ) -> Dict[str, Any]:
        """Process a clinical query using agentic RAG."""
        start_time = time.time()
        
        # Get patient context
        patient_context = await self.get_patient_context(db, patient_id)
        
        # Run all agents in parallel (simulated)
        research_agent = await self.clinical_research_agent(query, patient_context)
        history_agent = await self.patient_history_agent(query, patient_context) if include_history else None
        protocol_agent = await self.treatment_protocol_agent(query, patient_context)
        risk_agent = await self.risk_assessment_agent(query, patient_context)
        
        agent_responses = [research_agent, protocol_agent, risk_agent]
        if history_agent:
            agent_responses.append(history_agent)
        
        # Generate care plan
        care_plan = await self.generate_care_plan(query, patient_id, agent_responses)
        
        # Extract recommended tests
        recommended_tests = []
        for agent in agent_responses:
            for rec in agent.recommendations:
                if any(test in rec.lower() for test in ["ecg", "test", "lab", "imaging", "x-ray"]):
                    recommended_tests.append(rec)
        
        processing_time = time.time() - start_time
        
        return {
            "agent_responses": agent_responses,
            "care_plan": care_plan,
            "recommended_tests": recommended_tests[:5],
            "medication_recommendations": [],
            "risk_assessment": {
                "overall_risk": "moderate",
                "factors": [f.findings[0] if f.findings else "" for f in agent_responses],
            },
            "summary": f"Analysis complete for patient {patient_id}. {len(agent_responses)} agents analyzed the query.",
            "processing_time_seconds": processing_time,
        }

