from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from rti_agentic_system.config.database import get_db
from rti_agentic_system.models.schemas import RTIApplicationCreate, RTIApplicationResponse, RTIApplication
from rti_agentic_system.services.llm_orchestrator import run_guardrail, run_compliance_synthesis
from rti_agentic_system.services.embedding_router import search_index, add_to_index

router = APIRouter()

class IngestDoc(BaseModel):
    text: str

@router.post("/ingest")
def ingest_document(doc: IngestDoc):
    """Ingest documents into the local FAISS index for retrieval."""
    add_to_index([doc.text])
    return {"message": "Document ingested successfully"}

@router.post("/validate", response_model=RTIApplicationResponse)
def validate_and_create_application(application: RTIApplicationCreate, db: Session = Depends(get_db)):
    """Validates query via guardrail and creates record."""
    is_valid = run_guardrail(application.query_text)
    
    status = "RECEIVED" if is_valid else "REJECTED_BY_GUARDRAIL"
    
    db_app = RTIApplication(
        applicant_name=application.applicant_name,
        query_text=application.query_text,
        status=status
    )
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    
    if not is_valid:
        raise HTTPException(status_code=400, detail="Query rejected by guardrails.")
        
    return db_app

@router.post("/compile/{app_id}", response_model=RTIApplicationResponse)
def compile_response(app_id: int, db: Session = Depends(get_db)):
    """Synthesizes a response for a validated query."""
    db_app = db.query(RTIApplication).filter(RTIApplication.id == app_id).first()
    if not db_app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    if db_app.status == "REJECTED_BY_GUARDRAIL":
        raise HTTPException(status_code=400, detail="Cannot compile response for rejected application")
        
    # Retrieve context
    contexts = search_index(db_app.query_text, k=3)
    context_str = "\n".join(contexts)
    
    # Synthesize response
    response_text = run_compliance_synthesis(db_app.query_text, context_str)
    
    db_app.response_text = response_text
    db_app.status = "COMPLETED"
    
    db.commit()
    db.refresh(db_app)
    
    return db_app
