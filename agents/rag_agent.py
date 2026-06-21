import os
import json
import faiss
import pickle
import logging
from datetime import datetime
import numpy as np

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sentence_transformers import SentenceTransformer

from constants.app_constants import LLMConfig, FilePath
from schema.rag_schema import QueryClassification, QueryIntent
from utils.redis_cache import ConversationCache

logger = logging.getLogger(__name__)

class RagAgent:
    """Agent responsible for Retrieval-Augmented Generation (RAG) with intent routing and conversational cache."""
    
    def __init__(self):
        self.cache = ConversationCache()
        
        # Load LLM
        api_base = LLMConfig.OPENAI_API_BASE
        if api_base == "your_api_base_url_here" or not api_base:
            api_base = None
            
        api_key = LLMConfig.OPENAI_API_KEY
        if api_key == "your_api_key_here" or not api_key:
            logger.warning("OPENAI_API_KEY is not set. RagAgent will fail if a real key is not provided.")

        self.llm = ChatOpenAI(
            model=LLMConfig.MODEL_NAME,
            api_key=api_key,
            base_url=api_base,
            temperature=LLMConfig.TEMPERATURE
        )
        
        # Load Embedding Model
        logger.info("Loading sentence transformer model for RAG...")
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        # Load FAISS
        self.index_path = os.path.join("data", "atomic_queries.index")
        self.mapping_path = os.path.join("data", "id_mapping.pkl")
        
        self.index = None
        self.id_mapping = {}
        
        self._load_faiss_index()
        
        # Setup Prompts
        try:
            with open(FilePath.RAG_CLASSIFIER_PROMPT, 'r') as f:
                classifier_system = f.read().strip()
            with open(FilePath.RAG_SUMMARIZER_PROMPT, 'r') as f:
                summarizer_system = f.read().strip()
            with open(FilePath.RAG_SUGGESTION_PROMPT, 'r') as f:
                suggestion_system = f.read().strip()
        except FileNotFoundError as e:
            logger.error(f"Failed to load RAG prompts: {e}")
            classifier_system = "You are an intelligent router. Classify the user's intent into one of the exact categories provided. GREETING is for hellos. SUGGESTION is for asking how to handle something. QUERY is for factual/historical questions. OUT_OF_SCOPE is for completely unrelated topics. MALICIOUS is for attacks or harmful content. CRISIS is for self-harm or emergencies."
            summarizer_system = "You are an AI assistant for RTI queries. Summarize the following office note based on the user's query.\n\nOffice Note:\n{office_note}\n\nConversation History:\n{history}"
            suggestion_system = "You are an AI advisor. Based on the following top historical office notes, provide a clear suggestion on how the user should handle their current query.\n\nHistorical Notes:\n{notes}\n\nConversation History:\n{history}"

        self.classifier_prompt = ChatPromptTemplate.from_messages([
            ("system", classifier_system),
            ("human", "{query}")
        ])
        
        self.query_summarizer_prompt = ChatPromptTemplate.from_messages([
            ("system", summarizer_system),
            ("human", "{query}")
        ])
        
        self.suggestion_prompt = ChatPromptTemplate.from_messages([
            ("system", suggestion_system),
            ("human", "{query}")
        ])

    def _load_faiss_index(self):
        if os.path.exists(self.index_path) and os.path.exists(self.mapping_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.mapping_path, "rb") as f:
                    self.id_mapping = pickle.load(f)
                logger.info("Successfully loaded FAISS index and mapping.")
            except Exception as e:
                logger.error(f"Failed to load FAISS index: {e}")
        else:
            logger.warning(f"FAISS index or mapping not found in data/. Vector search will fail.")

    def evaluate_query(self, user_id: str, query: str) -> dict:
        """Main entry point. Classifies query, routes to handler, updates cache."""
        logger.info(f"RagAgent routing query for user {user_id}...")
        
        # Classify without context
        classifier_chain = self.classifier_prompt | self.llm.with_structured_output(QueryClassification)
        try:
            classification = classifier_chain.invoke({"query": query})
            intent = classification.intent
            logger.info(f"Query classified as: {intent.value}")
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            intent = QueryIntent.OUT_OF_SCOPE
            
        # Route
        result = None
        if intent == QueryIntent.MALICIOUS or intent == QueryIntent.CRISIS:
            result = {"answer": "I cannot answer this question as it violates safety guidelines or requires human intervention."}
            return result # Do not cache
            
        elif intent == QueryIntent.GREETING:
            result = {"answer": self._handle_greeting()}
            
        elif intent == QueryIntent.OUT_OF_SCOPE:
            result = {"answer": self._handle_out_of_scope()}
            
        elif intent == QueryIntent.QUERY:
            result = self._handle_query(user_id, query)
            
        elif intent == QueryIntent.SUGGESTION:
            result = self._handle_suggestion(user_id, query)
            
        # Update Cache
        if result and "answer" in result:
            self.cache.add_conversation_turn(user_id, query, result["answer"])
            
        return result

    def _handle_greeting(self) -> str:
        hour = datetime.now().hour
        if hour < 12:
            greeting = "Good Morning"
        elif 12 <= hour < 17:
            greeting = "Good Afternoon"
        else:
            greeting = "Good Evening"
        return f"{greeting}! How can I help you with your RTI queries today?"

    def _handle_out_of_scope(self) -> str:
        return (
            "I can't help with this query as this is out of my scope. "
            "Here are some sample questions I can answer:\n"
            "1. What is the status of my RTI application?\n"
            "2. How do I process a refund?\n"
            "3. Suggest a way to handle frozen cryptocurrency assets."
        )

    def _search_faiss(self, query: str, k: int) -> list:
        if not self.index:
            return []
        
        query_emb = self.embedding_model.encode([query])
        distances, indices = self.index.search(query_emb, k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx in self.id_mapping:
                results.append(self.id_mapping[idx])
        return results

    def _mock_fetch_db(self, atomic_query_id: str) -> dict:
        """Mock fetching office note and enclosure from relational DB."""
        return {
            "office_note": f"Mocked office note details for {atomic_query_id}. Action was taken according to section 4.",
            "enclosure": f"/path/to/mock_enclosure_{atomic_query_id}.pdf"
        }

    def _handle_query(self, user_id: str, query: str) -> dict:
        # 1. Search FAISS
        top_ids = self._search_faiss(query, k=1)
        if not top_ids:
            return {"answer": "No relevant historical records found for this query."}
            
        atomic_query_id = top_ids[0]
        
        # 2. Fetch DB
        db_data = self._mock_fetch_db(atomic_query_id)
        office_note = db_data["office_note"]
        enclosure = db_data["enclosure"]
        
        # 3. Fetch History
        history = self.cache.get_conversation_history(user_id)
        history_str = json.dumps(history, indent=2) if history else "No previous context."
        
        # 4. Summarize
        chain = self.query_summarizer_prompt | self.llm
        try:
            summary_msg = chain.invoke({"query": query, "office_note": office_note, "history": history_str})
            summary = summary_msg.content
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            summary = "Failed to generate summary."
            
        return {
            "answer": summary, # Used for cache
            "summary": summary,
            "office_note": office_note,
            "enclosure": enclosure,
            "atomic_query_id": atomic_query_id
        }

    def _handle_suggestion(self, user_id: str, query: str) -> dict:
        # 1. Search FAISS
        top_ids = self._search_faiss(query, k=3)
        if not top_ids:
            return {"answer": "No relevant historical records found to provide a suggestion."}
            
        # 2. Fetch DB notes
        notes = []
        for qid in top_ids:
            data = self._mock_fetch_db(qid)
            notes.append(f"[{qid}]: {data['office_note']}")
            
        combined_notes = "\n".join(notes)
        
        # 3. Fetch History
        history = self.cache.get_conversation_history(user_id)
        history_str = json.dumps(history, indent=2) if history else "No previous context."
        
        # 4. Synthesize suggestion
        chain = self.suggestion_prompt | self.llm
        try:
            suggestion_msg = chain.invoke({"query": query, "notes": combined_notes, "history": history_str})
            suggestion = suggestion_msg.content
        except Exception as e:
            logger.error(f"Suggestion synthesis failed: {e}")
            suggestion = "Failed to generate suggestion."
            
        return {
            "answer": suggestion,
            "suggestion": suggestion,
            "reference_ids": top_ids
        }

    def draft_office_note(self, query: str, precedents: str) -> str:
        try:
            chain = self.draft_note_prompt | self.llm | StrOutputParser()
            return chain.invoke({"query": query, "precedents": precedents})
        except Exception as e:
            logger.error(f"Error drafting office note: {e}")
            return "Failed to draft office note."
