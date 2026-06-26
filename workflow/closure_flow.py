import logging
import requests
import base64
from agents.drafting_agent import DraftingAgent
from constants.app_constants import MeeraEndpoints

logger = logging.getLogger(__name__)

class ClosureFlow:
    def __init__(self):
        self.drafting_agent = DraftingAgent()
        self.fetch_url = MeeraEndpoints.FETCH_ATOMIC_NOTES_API_URL

    def run(self, rti_id: str):
        logger.info(f"Starting Closure Flow for RTI {rti_id}")
        try:
            res = requests.get(self.fetch_url, params={"rti_query_id": rti_id})
            res.raise_for_status()
            data = res.json().get("data", [])
            
            print("********** DATA ****************** : ",data)
            
            notes_text = []
            for item in data:
                note_base64 = item.get("office_note_base64")
                if note_base64:
                    try:
                        decoded_bytes = base64.b64decode(note_base64)
                        note_content = decoded_bytes.decode('utf-8', errors='ignore')
                        if note_content:
                            notes_text.append(note_content)
                    except Exception as dec_err:
                        logger.error(f"Error decoding base64 office note: {dec_err}")
                
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
