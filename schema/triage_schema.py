from pydantic import BaseModel, Field

class TriageResult(BaseModel):
    thought_process: str = Field(description="Step-by-step reasoning evaluating the 3 criteria.")
    complies_guidelines: bool = Field(description="True if the query complies with the RTI filling guidelines (e.g. email/name present, structured logically).")
    under_rbi_purview: bool = Field(description="True if the RTI query comes under the purview of RBI.")
    is_gibberish: bool = Field(description="True if the RTI query is unintelligible gibberish, a rant, or a general opinion.")
