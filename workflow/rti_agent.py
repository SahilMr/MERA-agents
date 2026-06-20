import logging
import requests
from typing import TypedDict, List, Optional, Dict
from langgraph.graph import StateGraph, START, END

from agents.triage_agent import TriageAgent
from agents.decomposer_agent import DecomposerAgent
from agents.department_assignment_agent import DepartmentAssignmentAgent
from agents.mail_agent import MailAgent

from schema.triage_schema import TriageResult
from schema.decomposer_schema import DecomposedResult
from schema.department_schema import DepartmentAssignmentResult
from constants.app_constants import MeeraEndpoints

logger = logging.getLogger(__name__)

class GraphState(TypedDict):
    rti_id: str
    query: str
    applicant_email: Optional[str]
    triage_result: Optional[TriageResult]
    atomic_queries: Optional[List[str]]
    assignments: Optional[List[Dict[str, str]]]
    final_status: Optional[str]

class RTIAgentWorkflow:
    def __init__(self):
        self.triage_agent = TriageAgent()
        self.decomposer_agent = DecomposerAgent()
        self.dept_agent = DepartmentAssignmentAgent()
        self.mail_agent = MailAgent()
        
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(GraphState)

        workflow.add_node("triage", self.triage_node)
        workflow.add_node("request_missing_info", self.request_missing_info_node)
        workflow.add_node("mark_out_of_scope", self.mark_out_of_scope_node)
        workflow.add_node("decompose", self.decompose_node)
        workflow.add_node("assign_departments", self.assign_departments_node)
        workflow.add_node("store_assignments", self.store_assignments_node)

        workflow.add_edge(START, "triage")

        workflow.add_conditional_edges(
            "triage",
            self.route_triage,
            {
                "request_missing_info": "request_missing_info",
                "mark_out_of_scope": "mark_out_of_scope",
                "decompose": "decompose"
            }
        )

        workflow.add_edge("request_missing_info", END)
        workflow.add_edge("mark_out_of_scope", END)
        workflow.add_edge("decompose", "assign_departments")
        workflow.add_edge("assign_departments", "store_assignments")
        workflow.add_edge("store_assignments", END)

        return workflow.compile()

    def route_triage(self, state: GraphState) -> str:
        triage = state["triage_result"]
        if not triage.is_filed_properly:
            return "request_missing_info"
        if not triage.under_rti_purview:
            return "mark_out_of_scope"
        return "decompose"

    def triage_node(self, state: GraphState) -> dict:
        logger.info(f"Running Triage on RTI ID: {state['rti_id']}")
        result = self.triage_agent.evaluate_query(state["query"])
        return {"triage_result": result}

    def request_missing_info_node(self, state: GraphState) -> dict:
        rti_id = state["rti_id"]
        applicant_email = state.get("applicant_email")
        reasoning = state["triage_result"].reasoning
        
        if applicant_email:
            logger.info(f"Sending missing info email to {applicant_email}")
            self.mail_agent.dispatch_applicant_email(
                query_id=rti_id,
                applicant_email=applicant_email,
                missing_info_context=reasoning
            )
            return {"final_status": "email_sent_missing_info"}
        else:
            logger.info(f"No email provided for RTI {rti_id}. Adding remark to DB.")
            self._update_rti_status(rti_id, "MISSING_INFO_NO_EMAIL", reasoning)
            return {"final_status": "remark_added_no_email"}

    def mark_out_of_scope_node(self, state: GraphState) -> dict:
        rti_id = state["rti_id"]
        reasoning = state["triage_result"].reasoning
        logger.info(f"Marking RTI {rti_id} as out of scope.")
        self._update_rti_status(rti_id, "OUT_OF_SCOPE", reasoning)
        return {"final_status": "marked_out_of_scope"}

    def decompose_node(self, state: GraphState) -> dict:
        logger.info(f"Decomposing RTI {state['rti_id']}")
        result = self.decomposer_agent.evaluate_query(state["query"])
        return {"atomic_queries": result.atomic_queries}

    def assign_departments_node(self, state: GraphState) -> dict:
        logger.info(f"Assigning departments for RTI {state['rti_id']}")
        assignments = []
        for atomic in state["atomic_queries"]:
            dept_res = self.dept_agent.evaluate_query(atomic)
            assignments.append({
                "atomic_query": atomic,
                "department": dept_res.assigned_department
            })
        return {"assignments": assignments}

    def store_assignments_node(self, state: GraphState) -> dict:
        rti_id = state["rti_id"]
        assignments = state["assignments"]
        logger.info(f"Storing assignments for RTI {rti_id} in DB.")
        
        payload = {
            "rti_query_id": rti_id,
            "assignments": assignments
        }
        try:
            response = requests.post(MeeraEndpoints.STORE_ATOMIC_DEPARTMENT_API_URL, json=payload)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to store assignments in DB: {e}")
            
        return {"final_status": "assignments_stored"}

    def _update_rti_status(self, rti_id: str, status: str, remark: str):
        payload = {
            "rti_query_id": rti_id,
            "status": status,
            "remark": remark
        }
        try:
            response = requests.post(MeeraEndpoints.UPDATE_RTI_STATUS_API_URL, json=payload)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to update RTI status in DB: {e}")
