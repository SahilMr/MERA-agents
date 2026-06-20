import os
from dotenv import load_dotenv

# Load environment variables here so they are available immediately
load_dotenv()

# Base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class FilePath:
    SYSTEM_PROMPT = os.path.join(BASE_DIR, "prompts", "system_prompt.txt")
    TRIAGE_PROMPT = os.path.join(BASE_DIR, "prompts", "triage_prompt.txt")
    DECOMPOSER_PROMPT = os.path.join(BASE_DIR, "prompts", "decomposer_prompt.txt")
    MAIL_PROMPT = os.path.join(BASE_DIR, "prompts", "mail_prompt.txt")

class KafkaConfig:
    BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    TOPIC = os.getenv("KAFKA_TOPIC", "rti_topic")
    GROUP_ID = os.getenv("KAFKA_GROUP_ID", "rti_group")

class MeeraEndpoints:
    FETCH_RTI_REQUEST_URL = os.getenv("FETCH_RTI_QUERY_API_URL", "http://localhost:8000/api/fetch_rti_query")
    INSERT_MAIL_RECORD_API_URL = os.getenv("INSERT_MAIL_RECORD_API_URL", "http://localhost:8000/api/insert_mail_record")
    UPDATE_RTI_STATUS_API_URL = os.getenv("UPDATE_RTI_STATUS_API_URL", "http://localhost:8000/api/update_rti_status")
    STORE_ATOMIC_DEPARTMENT_API_URL = os.getenv("STORE_ATOMIC_DEPARTMENT_API_URL", "http://localhost:8000/api/store_atomic_department")

class MailConfig:
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASS = os.getenv("SMTP_PASS", "")

class LLMConfig:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")
    TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))
    BERT_MODEL_PATH = os.getenv("BERT_MODEL_PATH", "bert-base-uncased")
