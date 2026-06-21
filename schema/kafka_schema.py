from pydantic import BaseModel, Field
from typing import Optional

class RTIKafkaMessage(BaseModel):
    rti_id: str = Field(..., description="The ID of the RTI query passed in the message")
    applicant_name: Optional[str] = Field(..., description="The name of the applicant")
    applicant_mail: Optional[str] = Field(..., description="The email of the applicant")
    applicant_phone_number: Optional[str] = Field(..., description="The number of the applicant")
    query : Optional[str] = Field(..., description="The query of the applicant")
    date : str = Field(..., description="The date of the query")
 
    