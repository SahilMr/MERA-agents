from pydantic import BaseModel, Field
from enum import Enum

class QueryIntent(str, Enum):
    QUERY = "query"
    GREETING = "greeting"
    SUGGESTION = "suggestion"
    OUT_OF_SCOPE = "out_of_scope"
    MALICIOUS = "malicious"
    CRISIS = "crisis"

class QueryClassification(BaseModel):
    intent: QueryIntent = Field(description="The classified intent of the user's message.")
