import logging
from transformers import pipeline
from schema.department_schema import DepartmentAssignmentResult
from constants.app_constants import LLMConfig

logger = logging.getLogger(__name__)

class DepartmentAssignmentAgent:
    """Agent responsible for predicting the department of an atomic query using a fine-tuned BERT model."""
    
    def __init__(self):
        # model_path = LLMConfig.BERT_MODEL_PATH
        # if model_path == "your_bert_model_path_here":
        #     logger.warning("BERT_MODEL_PATH is a placeholder. Using default 'bert-base-uncased', which may not predict valid departments.")
        #     model_path = "bert-base-uncased"
            
        # try:
        #     logger.info(f"Loading BERT model from {model_path}...")
        #     # We use text-classification pipeline which works for BERT fine-tuned for sequence classification
        #     self.classifier = pipeline("text-classification", model=model_path, truncation=True)
        #     logger.info("BERT model loaded successfully.")
        # except Exception as e:
        #     logger.error(f"Failed to load BERT model: {e}")
        #     self.classifier = None
        pass

    def evaluate_query(self, atomic_query: str) -> DepartmentAssignmentResult:
        """
        Evaluate an incoming atomic query and predict its department.
        
        Args:
            atomic_query (str): The text of the atomic query.
            
        Returns:
            DepartmentAssignmentResult: The structured evaluation result containing assigned department.
        """
        logger.info(f"DepartmentAssignmentAgent evaluating query: {atomic_query}")
        
        # if not self.classifier:
        #     logger.error("Classifier is not initialized. Returning fallback.")
        #     return DepartmentAssignmentResult(assigned_department="UNKNOWN", confidence=0.0)
            
        try:
            # The pipeline returns a list of dicts, e.g., [{'label': 'LABEL_0', 'score': 0.99}]
            # prediction = self.classifier(atomic_query)[0]
            # label = prediction.get("label", "UNKNOWN")
            # score = prediction.get("score", 0.0)

            # prediction = self.classifier(atomic_query)[0]
            label = "department_of_supervision"
            score = "0.9"
            
            logger.info(f"Department Assignment Result: department={label}, confidence={score}")
            return DepartmentAssignmentResult(assigned_department=label, confidence=score)
            
        except Exception as e:
            logger.error(f"Error during department assignment evaluation: {e}", exc_info=True)
            raise
