from pydantic import BaseModel, Field

class RTIKafkaMessage(BaseModel):
    rti_id: str = Field(..., description="The ID of the RTI query passed in the message")
    applicant_name: str = Field(..., description="The name of the applicant")
    applicant_mail: str = Field(..., description="The email of the applicant")
    applicant_phone_number: str = Field(..., description="The number of the applicant")
    query : str = Field(..., description="The query of the applicant")
    date : str = Field(..., description="The date of the query")
 
    