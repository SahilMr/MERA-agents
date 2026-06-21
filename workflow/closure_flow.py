import logging
import requests
from agents.drafting_agent import DraftingAgent
from constants.app_constants import MeeraEndpoints
import os

logger = logging.getLogger(__name__)

class ClosureFlow:
    def __init__(self):
        self.drafting_agent = DraftingAgent()
        self.fetch_url = MeeraEndpoints.FETCH_RTI_REQUEST_URL.replace("fetch_rti_query", "") 
        # Actually it's better to fetch by ID using the detail endpoint: /rti-queries/{rti_id}
        # Assuming we have an endpoint for this. We will just hardcode the base url for now
        api_base = os.getenv("CREATE_RTI_QUERY_API_URL", "http://127.0.0.1:8000/api/v1/rti-queries")
        # remove any trailing slash
        if api_base.endswith('/'):
            api_base = api_base[:-1]
        self.detail_url = api_base

    def run(self, rti_id: str):
        logger.info(f"Starting Closure Flow for RTI {rti_id}")
        try:
            res = requests.get(f"{self.detail_url}/{rti_id}")
            res.raise_for_status()
            data = res.json().get("data", {})
            
            office_notes = data.get("office_notes", [])
            notes_text = []
            for n in office_notes:
                notes_text.append(n.get("office_note", ""))
                
            if not notes_text:
                logger.warning(f"No office notes found for RTI {rti_id}. Cannot collate.")
                return
                
            success = self.drafting_agent.draft_closure_response(rti_id, notes_text)
            if success:
                logger.info(f"Closure Flow completed successfully for RTI {rti_id}")
            else:
                logger.error(f"Drafting agent failed to upload closure response for RTI {rti_id}")
                
        except Exception as e:
            logger.error(f"Error in Closure Flow for RTI {rti_id}: {e}", exc_info=True)
