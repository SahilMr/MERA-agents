from pydantic import BaseModel, Field

class RTIKafkaMessage(BaseModel):
    rti_id: str = Field(..., description="The ID of the RTI query passed in the message")
