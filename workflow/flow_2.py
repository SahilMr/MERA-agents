import logging
from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END
import requests
import datetime
from datetime import timedelta

from agents.triage_agent import TriageAgent
from agents.decomposer_agent import DecomposerAgent
from agents.department_assignment_agent import DepartmentAssignmentAgent
from agents.drafting_agent import DraftingAgent
from constants.app_constants import MeeraEndpoints

logger = logging.getLogger(__name__)

class GraphState(TypedDict):
    rti_id: str
    query: str
    applicant_email: str
    triage_result: dict
    atomic_queries: List[str]
    assignments: List[dict]


class Flow2Workflow:
    def __init__(self):
        self.triage_agent = TriageAgent()
        self.decomposer_agent = DecomposerAgent()
        self.dept_agent = DepartmentAssignmentAgent()
        self.drafting_agent = DraftingAgent()
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(GraphState)

        workflow.add_node("validation", self.validation_node)
        workflow.add_node("drafting_revision", self.drafting_revision_node)
        workflow.add_node("decompose", self.decompose_node)
        workflow.add_node("assign_and_insert", self.assign_and_insert_node)

        workflow.set_entry_point("validation")

        workflow.add_conditional_edges(
            "validation",
            self.route_validation,
            {
                "drafting_revision": "drafting_revision",
                "decompose": "decompose"
            }
        )

        workflow.add_edge("drafting_revision", END)
        workflow.add_edge("decompose", "assign_and_insert")
        workflow.add_edge("assign_and_insert", END)

        return workflow.compile()

    def route_validation(self, state: GraphState) -> str:
        triage = state["triage_result"]
        logger.info(f"*********** VALIDATION : ************** {triage}")
        if not triage.complies_guidelines or triage.is_gibberish:
            return "drafting_revision"
        if not triage.under_rbi_purview:
            return "drafting_revision"
        return "decompose"

    def validation_node(self, state: GraphState) -> dict:
        logger.info(f"Running Validation on RTI ID: {state['rti_id']}")
        result = self.triage_agent.evaluate_query(state["query"])
        return {"triage_result": result}

    def drafting_revision_node(self, state: GraphState) -> dict:
        rti_id = state["rti_id"]
        triage = state["triage_result"]
        
        status_id = 5
        if not triage.under_rbi_purview and triage.complies_guidelines and not triage.is_gibberish:
            status_id = 4
            
        reasoning = triage.thought_process
        logger.info(f"Validation failed for RTI {rti_id}. Routing to Drafting Agent. Status: {status_id}")
        
        self.drafting_agent.draft_revision_response(rti_id, reasoning, status_id)
        return {}

    def decompose_node(self, state: GraphState) -> dict:
        logger.info(f"Decomposing RTI {state['rti_id']}")
        result = self.decomposer_agent.evaluate_query(state["query"])
        return {"atomic_queries": result.atomic_queries}

    def assign_and_insert_node(self, state: GraphState) -> dict:
        logger.info(f"Assigning departments and inserting for RTI {state['rti_id']}")
        assignments = []
        
        grouped_queries = {}
        for atomic in state["atomic_queries"]:
            dept_res = self.dept_agent.evaluate_query(atomic)
            dept = dept_res.assigned_department
            if dept not in grouped_queries:
                grouped_queries[dept] = []
            grouped_queries[dept].append(atomic)
            
        for dept, queries in grouped_queries.items():
            combined_query = " | ".join(queries)
            try:
                # 1. Fetch Mapping
                mapping_payload = {
                    "department": dept
                }
                mapping_res = requests.get(MeeraEndpoints.FETCH_MAPPING_API_URL, params=mapping_payload)
                mapping_res.raise_for_status()
                mapping_data = mapping_res.json()
                records = mapping_data.get("data", {}).get("records", [])
                if not records:
                    logger.error(f"No records found in mapping for department {dept}")
                    continue
                record = records[0]
                user_id = record.get("id")
                
                # 2. Create Inward
                inward_payload = {
                    "department": record.get("department"),
                    "inward_file": combined_query,
                    "user_name": record.get("user"),
                    "division": record.get("division_section"),
                    "sub_section": record.get("sub_section"),
                    "case_access_level": "Wider Case Access",
                    "privacy_level": "public",
                    "inward_priority_level": "high",
                    "year": str(datetime.date.today().year),
                    "inward_subject": "RTI Atomic Query",
                    "inward_type": "TBD",
                    "from_which_office": "Central Office",
                    "from_which_department": record.get("department"),
                    "inward_date": str(datetime.date.today()),
                    "letter_type": "Central Office(Others)",
                    "estimated_date_of_closure": str(datetime.date.today() + timedelta(days=30)),
                    "date_of_receipt": str(datetime.date.today()),
                    "process_type": "RTI",
                    "letter_language": "English",
                    "assigned_to": "self"
                }
                inward_res = requests.post(MeeraEndpoints.CREATE_INWARD_API_URL, json=inward_payload)
                inward_res.raise_for_status()
                inward_id = inward_res.json().get("data", {}).get("inward_id")

                # 3. Insert Atomic Query
                atomic_payload = {
                    "rti_query_id": state["rti_id"],
                    "atomic_query": combined_query,
                    "department_id": str(user_id),
                    "inward_id": inward_id
                }
                atomic_res = requests.post(MeeraEndpoints.INSERT_ATOMIC_QUERY_API_URL, json=atomic_payload)
                atomic_res.raise_for_status()
                atomic_query_id = atomic_res.json().get("data", {}).get("atomic_query_id")

                assignments.append({
                    "atomic_query_id": atomic_query_id,
                    "query": combined_query,
                    "department": dept,
                    "inward_id": inward_id
                })

            except Exception as e:
                logger.error(f"Failed pipeline for department {dept}: {e}", exc_info=True)
                
        return {"assignments": assignments}

 