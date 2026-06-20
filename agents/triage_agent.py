import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from schema.triage_schema import TriageResult
from constants.app_constants import LLMConfig, FilePath

logger = logging.getLogger(__name__)

class TriageAgent:
    """Agent responsible for triaging incoming RTI queries."""
    
    def __init__(self):
        # Initialize the LLM with configurations from constants
        # If OPENAI_API_BASE is empty/placeholder, we let langchain use the default.
        api_base = LLMConfig.OPENAI_API_BASE
        if api_base == "your_api_base_url_here" or not api_base:
            api_base = None
            
        api_key = LLMConfig.OPENAI_API_KEY
        if api_key == "your_api_key_here" or not api_key:
            logger.warning("OPENAI_API_KEY is not set or is a placeholder. TriageAgent will fail if a real key is not provided.")

        self.llm = ChatOpenAI(
            model=LLMConfig.MODEL_NAME,
            api_key=api_key,
            base_url=api_base,
            temperature=LLMConfig.TEMPERATURE
        )
        
        # Load the triage prompt
        try:
            with open(FilePath.TRIAGE_PROMPT, 'r') as f:
                system_prompt = f.read()
        except FileNotFoundError:
            logger.error(f"Triage prompt file not found at {FilePath.TRIAGE_PROMPT}")
            system_prompt = "You are an RTI triage agent. Evaluate if the query is valid."
            
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "RTI Query:\n{query}")
        ])
        
        # Create the structured output runnable
        self.chain = self.prompt | self.llm.with_structured_output(TriageResult)

    def evaluate_query(self, query: str) -> TriageResult:
        """
        Evaluate an incoming RTI query.
        
        Args:
            query (str): The text of the RTI query.
            
        Returns:
            TriageResult: The structured evaluation result.
        """
        logger.info("TriageAgent evaluating query...")
        try:
            result = self.chain.invoke({"query": query})
            logger.info(f"Triage Result: should_route={result.should_route}, reasoning={result.reasoning}")
            return result
        except Exception as e:
            logger.error(f"Error during triage evaluation: {e}", exc_info=True)
            raise

