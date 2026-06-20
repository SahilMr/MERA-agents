from pydantic import BaseModel, Field
from typing import List

class DecomposedResult(BaseModel):
    is_multi_part: bool = Field(description="True if the original query contained multiple distinct questions or requests.")
    atomic_queries: List[str] = Field(description="A list of standalone, atomic queries extracted from the original query. If it is not multi-part, this list should contain just the original query.")
    reasoning: str = Field(description="Brief explanation of why the query was broken down the way it was.")
