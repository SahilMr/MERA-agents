from pydantic import BaseModel, Field

class DepartmentAssignmentResult(BaseModel):
    assigned_department: str = Field(description="The department assigned by the BERT model.")
    confidence: float = Field(default=1.0, description="Confidence score from the model.")
