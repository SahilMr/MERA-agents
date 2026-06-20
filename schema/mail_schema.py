from pydantic import BaseModel, Field

class MailDraftResult(BaseModel):
    recipient_type: str = Field(description="'applicant', 'higher_up', or 'nodal_officer'")
    subject: str = Field(description="A concise and professional email subject line.")
    body: str = Field(description="The professional email body drafted.")
