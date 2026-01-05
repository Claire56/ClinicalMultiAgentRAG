"""Script to seed Pinecone with medical knowledge base."""
import sys
from pathlib import Path
import asyncio

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain.schema import Document
from app.services.pinecone_service import PineconeService
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)


# Sample medical knowledge base documents
MEDICAL_KNOWLEDGE = [
    {
        "content": """
        Chest Pain Evaluation Protocol:
        - All patients with chest pain require immediate ECG and troponin levels
        - Diabetic patients with chest pain have higher risk and need urgent cardiac evaluation
        - Consider non-cardiac causes: GERD, anxiety, musculoskeletal pain
        - Risk factors include: age > 65, diabetes, hypertension, family history of CAD
        - If initial workup negative, consider stress test or cardiac imaging
        """,
        "metadata": {"source": "Cardiology Guidelines", "type": "protocol", "category": "cardiac"},
    },
    {
        "content": """
        Diabetes Management Guidelines:
        - HbA1c should be checked every 3-6 months
        - Target HbA1c < 7% for most patients, < 8% for elderly or high-risk
        - Monitor for complications: retinopathy (annual eye exam), nephropathy (urine microalbumin), neuropathy (foot exam)
        - Blood pressure target: < 140/90 mmHg
        - Lipid management: statin therapy for most diabetic patients
        """,
        "metadata": {"source": "Endocrinology Guidelines", "type": "guideline", "category": "diabetes"},
    },
    {
        "content": """
        Hypertension Treatment Protocol:
        - Lifestyle modifications first: diet, exercise, weight loss
        - First-line medications: ACE inhibitors, ARBs, or calcium channel blockers
        - Target BP: < 130/80 for most patients, < 140/90 for elderly
        - Monitor for side effects: cough (ACE inhibitors), hyperkalemia, renal function
        - Consider combination therapy if single agent insufficient
        """,
        "metadata": {"source": "Cardiology Guidelines", "type": "protocol", "category": "hypertension"},
    },
    {
        "content": """
        Medication Interaction Warnings:
        - ACE inhibitors + potassium-sparing diuretics: risk of hyperkalemia
        - Warfarin + many antibiotics: increased bleeding risk
        - Metformin + contrast dye: risk of lactic acidosis, hold 48 hours before/after
        - Statins + certain antibiotics: increased risk of myopathy
        - Always check for drug-drug interactions before prescribing
        """,
        "metadata": {"source": "Pharmacy Guidelines", "type": "safety", "category": "medications"},
    },
    {
        "content": """
        Risk Stratification for Elderly Patients:
        - Age > 65 increases risk for complications
        - Consider more conservative treatment approaches
        - Monitor for polypharmacy and drug interactions
        - Assess functional status and comorbidities
        - Consider frailty assessment for major procedures
        """,
        "metadata": {"source": "Geriatrics Guidelines", "type": "guideline", "category": "elderly"},
    },
    {
        "content": """
        Chest Pain in Diabetic Patients:
        - Diabetic patients may have atypical chest pain presentation
        - Silent ischemia is more common in diabetic patients
        - Higher risk of multi-vessel disease
        - Require more aggressive cardiac evaluation
        - Consider early cardiology consultation
        """,
        "metadata": {"source": "Cardiology Guidelines", "type": "guideline", "category": "cardiac_diabetes"},
    },
    {
        "content": """
        Lab Test Ordering Guidelines:
        - ECG: immediate for chest pain, syncope, palpitations
        - Troponin: serial measurements for suspected MI (0, 3, 6 hours)
        - HbA1c: every 3-6 months for diabetes, annually for pre-diabetes
        - Lipid panel: baseline, then every 5 years if normal
        - Basic metabolic panel: assess renal function before contrast or nephrotoxic drugs
        """,
        "metadata": {"source": "Lab Guidelines", "type": "protocol", "category": "laboratory"},
    },
    {
        "content": """
        Follow-up Care Planning:
        - High-risk patients: follow-up within 24-48 hours
        - Moderate risk: follow-up within 1 week
        - Low risk: follow-up within 2-4 weeks
        - Ensure patient understands discharge instructions
        - Schedule appropriate specialist referrals
        - Provide clear medication instructions
        """,
        "metadata": {"source": "Care Coordination Guidelines", "type": "protocol", "category": "followup"},
    },
]


async def seed_pinecone():
    """Seed Pinecone with medical knowledge base."""
    logger.info("Starting Pinecone seeding...")
    
    if not settings.PINECONE_API_KEY:
        logger.error("Pinecone API key not set. Cannot seed database.")
        return
    
    pinecone_service = PineconeService()
    
    if not pinecone_service.vector_store:
        logger.error("Pinecone vector store not initialized. Check configuration.")
        return
    
    # Convert to Document objects
    documents = [
        Document(
            page_content=doc["content"].strip(),
            metadata=doc["metadata"],
        )
        for doc in MEDICAL_KNOWLEDGE
    ]
    
    try:
        # Add documents to Pinecone
        # Split into namespaces for better organization
        guideline_docs = [d for d in documents if d.metadata.get("type") == "guideline"]
        protocol_docs = [d for d in documents if d.metadata.get("type") == "protocol"]
        safety_docs = [d for d in documents if d.metadata.get("type") == "safety"]
        
        if guideline_docs:
            await pinecone_service.add_documents(guideline_docs, namespace="medical_guidelines")
            logger.info(f"Added {len(guideline_docs)} guideline documents")
        
        if protocol_docs:
            await pinecone_service.add_documents(protocol_docs, namespace="treatment_protocols")
            logger.info(f"Added {len(protocol_docs)} protocol documents")
        
        if safety_docs:
            await pinecone_service.add_documents(safety_docs, namespace="safety_guidelines")
            logger.info(f"Added {len(safety_docs)} safety documents")
        
        logger.info("✅ Pinecone seeding completed successfully!")
        logger.info(f"Total documents added: {len(documents)}")
        
    except Exception as e:
        logger.error("Failed to seed Pinecone", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(seed_pinecone())

