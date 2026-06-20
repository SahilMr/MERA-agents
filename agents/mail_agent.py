import logging
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from schema.mail_schema import MailDraftResult
from constants.app_constants import LLMConfig, FilePath, MailConfig, MeeraEndpoints

logger = logging.getLogger(__name__)

class MailAgent:
    """Agent responsible for drafting professional emails and sending them via SMTP."""
    
    def __init__(self):
        api_base = LLMConfig.OPENAI_API_BASE
        if api_base == "your_api_base_url_here" or not api_base:
            api_base = None
            
        api_key = LLMConfig.OPENAI_API_KEY
        if api_key == "your_api_key_here" or not api_key:
            logger.warning("OPENAI_API_KEY is not set. MailAgent will fail if a real key is not provided.")

        self.llm = ChatOpenAI(
            model=LLMConfig.MODEL_NAME,
            api_key=api_key,
            base_url=api_base,
            temperature=LLMConfig.TEMPERATURE
        )
        
        try:
            with open(FilePath.MAIL_PROMPT, 'r') as f:
                system_prompt = f.read()
        except FileNotFoundError:
            logger.error(f"Mail prompt file not found at {FilePath.MAIL_PROMPT}")
            system_prompt = "Draft a professional email."
            
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Recipient Type: {recipient_type}\nContext:\n{context}")
        ])
        
        self.chain = self.prompt | self.llm.with_structured_output(MailDraftResult)

    def _send_email(self, to_email: str, subject: str, body: str, attachment_path: str = None) -> str:
        """Internal helper to physically send an email using SMTP."""
        if not MailConfig.SMTP_USER or not MailConfig.SMTP_PASS:
            logger.error("SMTP credentials not configured.")
            return "Failed: SMTP credentials not configured."

        msg = MIMEMultipart()
        msg['From'] = MailConfig.SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        if attachment_path:
            try:
                # Mocking DB read or file read for attachment
                part = MIMEApplication(b"Mock Office Note PDF Content", Name="office_note.pdf")
                part['Content-Disposition'] = 'attachment; filename="office_note.pdf"'
                msg.attach(part)
            except Exception as e:
                logger.error(f"Failed to attach file: {e}")
                return f"Failed to attach file: {e}"

        try:
            server = smtplib.SMTP(MailConfig.SMTP_HOST, MailConfig.SMTP_PORT)
            server.starttls()
            server.login(MailConfig.SMTP_USER, MailConfig.SMTP_PASS)
            server.send_message(msg)
            server.quit()
            logger.info("Email sent successfully via SMTP.")
            return "Email sent successfully"
        except Exception as e:
            logger.error(f"SMTP error: {e}")
            return f"Failed to send email: {e}"

    def _log_email_record(self, query_id: str, recipient: str, status: str) -> str:
        """Internal helper to log the email dispatch to the DB API."""
        payload = {
            "rti_query_id": query_id,
            "recipient": recipient,
            "status": status
        }
        try:
            response = requests.post(MeeraEndpoints.INSERT_MAIL_RECORD_API_URL, json=payload)
            response.raise_for_status()
            logger.info(f"Logged email record for query {query_id}.")
            return f"Record logged successfully for query {query_id}"
        except Exception as e:
            logger.error(f"Failed to log email record: {e}")
            return f"Failed to log email record: {e}"

    # ------------------ DRAFTING ONLY ------------------

    def draft_applicant_email(self, query_id: str, missing_info_context: str) -> MailDraftResult:
        context = f"RTI Query ID: {query_id}\nWe need the following missing information: {missing_info_context}"
        return self._draft_email("applicant", context)

    def draft_approval_email(self, rti_ref: str, office_note_context: str) -> MailDraftResult:
        context = f"RTI Reference: {rti_ref}\nPlease review and approve the attached office note regarding: {office_note_context}"
        return self._draft_email("higher_up", context)

    def draft_nodal_officer_email(self, rti_ref: str, applicant_details: str) -> MailDraftResult:
        context = f"RTI Reference: {rti_ref}\nApplicant: {applicant_details}\nThe office note has been approved. Please find it attached and forward it to the applicant."
        return self._draft_email("nodal_officer", context)

    def _draft_email(self, recipient_type: str, context: str) -> MailDraftResult:
        logger.info(f"MailAgent drafting email for {recipient_type}...")
        try:
            result = self.chain.invoke({
                "recipient_type": recipient_type,
                "context": context
            })
            logger.info("Drafted email successfully.")
            return result
        except Exception as e:
            logger.error(f"Error drafting email: {e}", exc_info=True)
            raise

    # ------------------ DRAFT & DISPATCH ------------------

    def dispatch_applicant_email(self, query_id: str, applicant_email: str, missing_info_context: str):
        """Drafts AND sends the email to the applicant."""
        draft = self.draft_applicant_email(query_id, missing_info_context)
        result = self._send_email(applicant_email, draft.subject, draft.body)
        self._log_email_record(query_id, "applicant", result)
        return {"draft": draft, "dispatch_status": result}

    def dispatch_approval_email(self, rti_ref: str, higher_up_email: str, office_note_context: str):
        """Drafts AND sends the email to the higher-ups."""
        draft = self.draft_approval_email(rti_ref, office_note_context)
        result = self._send_email(higher_up_email, draft.subject, draft.body)
        self._log_email_record(rti_ref, "higher_up", result)
        return {"draft": draft, "dispatch_status": result}

    def dispatch_nodal_officer_email(self, rti_ref: str, nodal_email: str, applicant_details: str, attachment_id: str):
        """Drafts AND sends the email to the nodal officer."""
        draft = self.draft_nodal_officer_email(rti_ref, applicant_details)
        result = self._send_email(nodal_email, draft.subject, draft.body, attachment_path=attachment_id)
        self._log_email_record(rti_ref, "nodal_officer", result)
        return {"draft": draft, "dispatch_status": result}
