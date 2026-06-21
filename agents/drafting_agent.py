import logging
import requests
from fpdf import FPDF
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from constants.app_constants import LLMConfig, MeeraEndpoints

logger = logging.getLogger(__name__)

class DraftingAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=LLMConfig.MODEL_NAME,
            temperature=LLMConfig.TEMPERATURE,
            openai_api_key=LLMConfig.OPENAI_API_KEY,
            openai_api_base=LLMConfig.OPENAI_API_BASE
        )
        self.revision_prompt = PromptTemplate.from_template(
            "Draft a formal letter to an RTI applicant explaining that their request cannot be processed.\n"
            "Reason: {reason}\n\n"
            "The letter should be polite, professional, and clear. Do not include any placeholders like [Applicant Name] unless you have to, just write the body of the letter."
        )
        self.closure_prompt = PromptTemplate.from_template(
            "You are a professional assistant at the Reserve Bank of India (RBI).\n"
            "Below are several office notes related to different parts of an RTI query.\n"
            "Please collate these notes into a single cohesive final response to the applicant.\n\n"
            "Office Notes:\n{notes}\n\n"
            "Draft the final response letter:"
        )

    def _create_pdf(self, text: str) -> bytes:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(0, 10, text)
        return pdf.output(dest='S')

    def draft_revision_response(self, rti_query_id: str, reason: str, status_id: int) -> bool:
        logger.info(f"Drafting revision response for RTI {rti_query_id}")
        chain = self.revision_prompt | self.llm | StrOutputParser()
        draft_text = chain.invoke({"reason": reason})
        
        pdf_bytes = self._create_pdf(draft_text)
        
        try:
            files = {
                'collated_office_note': ('response.pdf', pdf_bytes, 'application/pdf')
            }
            data = {
                'rti_query_id': rti_query_id,
                'status_id': str(status_id),
                'remark': reason,
                'updated_by': 'DraftingAgent'
            }
            res = requests.put(MeeraEndpoints.UPDATE_RTI_QUERY_API_URL, data=data, files=files)
            res.raise_for_status()
            logger.info("Successfully updated RTI query with revision response.")
            return True
        except Exception as e:
            logger.error(f"Failed to upload revision response: {e}")
            return False

    def draft_closure_response(self, rti_query_id: str, notes: list) -> bool:
        logger.info(f"Drafting closure response for RTI {rti_query_id}")
        notes_str = "\n".join([f"- {note}" for note in notes])
        chain = self.closure_prompt | self.llm | StrOutputParser()
        draft_text = chain.invoke({"notes": notes_str})
        
        pdf_bytes = self._create_pdf(draft_text)
        
        try:
            files = {
                'collated_office_note': ('closure.pdf', pdf_bytes, 'application/pdf')
            }
            data = {
                'rti_query_id': rti_query_id,
                'updated_by': 'DraftingAgent'
            }
            res = requests.put(MeeraEndpoints.UPDATE_RTI_QUERY_API_URL, data=data, files=files)
            res.raise_for_status()
            logger.info("Successfully updated RTI query with closure response.")
            return True
        except Exception as e:
            logger.error(f"Failed to upload closure response: {e}")
            return False
