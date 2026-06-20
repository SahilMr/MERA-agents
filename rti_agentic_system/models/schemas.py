from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from rti_agentic_system.config.database import Base

# --- SQLAlchemy Models ---
class RTIApplication(Base):
    __tablename__ = "rti_applications"

    id = Column(Integer, primary_key=True, index=True)
    applicant_name = Column(String, index=True)
    query_text = Column(Text, nullable=False)
    status = Column(String, default="RECEIVED")
    created_at = Column(DateTime, default=datetime.utcnow)
    response_text = Column(Text, nullable=True)


# --- Pydantic Schemas ---
class RTIApplicationCreate(BaseModel):
    applicant_name: str
    query_text: str

class RTIApplicationResponse(BaseModel):
    id: int
    applicant_name: str
    query_text: str
    status: str
    response_text: str | None = None
    
    class Config:
        from_attributes = True
