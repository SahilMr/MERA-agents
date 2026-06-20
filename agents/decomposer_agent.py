import logging
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from schema.decomposer_schema import DecomposedResult
from constants.app_constants import LLMConfig, FilePath

logger = logging.getLogger(__name__)

class DecomposerAgent:
    """Agent responsible for breaking down multi-part RTI queries into atomic queries."""
    
    def __init__(self):
        # Initialize the LLM with configurations from constants
        api_base = LLMConfig.OPENAI_API_BASE
        if api_base == "your_api_base_url_here" or not api_base:
            api_base = None
            
        api_key = LLMConfig.OPENAI_API_KEY
        if api_key == "your_api_key_here" or not api_key:
            logger.warning("OPENAI_API_KEY is not set or is a placeholder. DecomposerAgent will fail if a real key is not provided.")

        self.llm = ChatOpenAI(
            model=LLMConfig.MODEL_NAME,
            api_key=api_key,
            base_url=api_base,
            temperature=LLMConfig.TEMPERATURE
        )
        
        # Load the decomposer prompt
        try:
            with open(FilePath.DECOMPOSER_PROMPT, 'r') as f:
                system_prompt = f.read()
        except FileNotFoundError:
            logger.error(f"Decomposer prompt file not found at {FilePath.DECOMPOSER_PROMPT}")
            system_prompt = "You are an RTI decomposer agent. Break down the query into atomic parts."
            
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "RTI Query:\n{query}")
        ])
        
        # Create the structured output runnable
        self.chain = self.prompt | self.llm.with_structured_output(DecomposedResult)

    def evaluate_query(self, query: str) -> DecomposedResult:
        """
        Evaluate an incoming RTI query and decompose it if necessary.
        
        Args:
            query (str): The text of the RTI query.
            
        Returns:
            DecomposedResult: The structured evaluation result containing atomic queries.
        """
        logger.info("DecomposerAgent evaluating query...")
        try:
            result = self.chain.invoke({"query": query})
            logger.info(f"Decomposer Result: is_multi_part={result.is_multi_part}, atomic_queries_count={len(result.atomic_queries)}")
            return result
        except Exception as e:
            logger.error(f"Error during decomposer evaluation: {e}", exc_info=True)
            raise
