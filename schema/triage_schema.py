from pydantic import BaseModel, Field

class TriageResult(BaseModel):
    is_filed_properly: bool = Field(description="True if the RTI query is filed with correct structure and required details.")
    under_rti_purview: bool = Field(description="True if the requested information falls under the purview of the Right to Information Act.")
    is_opinion_or_gibberish: bool = Field(description="True if the query is an opinion, feedback, or unintelligible gibberish.")
    should_route: bool = Field(description="True ONLY IF is_filed_properly AND under_rti_purview are True, AND is_opinion_or_gibberish is False.")
    reasoning: str = Field(description="A brief explanation for the decisions made.")
