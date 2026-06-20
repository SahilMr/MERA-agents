import os
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv("secret.env")

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0)

GUARDRAIL_PROMPT = PromptTemplate(
    input_variables=["query"],
    template="""You are a strict guardrail for an RTI (Right to Information) processing system.
Analyze the following user query and determine if it is appropriate for RTI submission.
If it contains abusive language, asks for highly classified state secrets, or is complete gibberish, return "REJECTED".
Otherwise, return "ACCEPTED".

Query: {query}
Result (ACCEPTED or REJECTED):"""
)

COMPLIANCE_PROMPT = PromptTemplate(
    input_variables=["query", "context"],
    template="""You are an expert in RTI compliance. Based on the user query and the retrieved context,
synthesize a comprehensive response. Ensure the response strictly adheres to the provided context.
If the context does not contain enough information to answer the query, clearly state that the requested information is not available in the current records.

Query: {query}

Context:
{context}

Response:"""
)

def run_guardrail(query: str) -> bool:
    chain = GUARDRAIL_PROMPT | llm
    result = chain.invoke({"query": query})
    return "ACCEPTED" in result.content.upper()

def run_compliance_synthesis(query: str, context: str) -> str:
    chain = COMPLIANCE_PROMPT | llm
    result = chain.invoke({"query": query, "context": context})
    return result.content
