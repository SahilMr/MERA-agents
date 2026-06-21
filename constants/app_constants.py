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
    RAG_CLASSIFIER_PROMPT = os.path.join(BASE_DIR, "prompts", "rag_classifier_prompt.txt")
    RAG_SUMMARIZER_PROMPT = os.path.join(BASE_DIR, "prompts", "rag_summarizer_prompt.txt")
    RAG_SUGGESTION_PROMPT = os.path.join(BASE_DIR, "prompts", "rag_suggestion_prompt.txt")

class KafkaConfig:
    BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    TOPIC = os.getenv("KAFKA_TOPIC", "rti_topic")
    GROUP_ID = os.getenv("KAFKA_GROUP_ID", "rti_group")

class MeeraEndpoints:
    FETCH_RTI_REQUEST_URL = os.getenv("FETCH_RTI_QUERY_API_URL", "http://localhost:8000/api/fetch_rti_query")
    INSERT_MAIL_RECORD_API_URL = os.getenv("INSERT_MAIL_RECORD_API_URL", "http://localhost:8000/api/insert_mail_record")
    UPDATE_RTI_STATUS_API_URL = os.getenv("UPDATE_RTI_STATUS_API_URL", "http://localhost:8000/api/update_rti_status")
    UPDATE_RTI_STATUS_API_URL = os.getenv("UPDATE_RTI_STATUS_API_URL", "http://localhost:8000/api/update_rti_status")
    FETCH_MAPPING_API_URL = os.getenv("FETCH_MAPPING_API_URL", "http://localhost:8000/api/fetch_mapping")
    INSERT_ATOMIC_QUERY_API_URL = os.getenv("INSERT_ATOMIC_QUERY_API_URL", "http://localhost:8000/api/insert_atomic_query")
    CREATE_INWARD_API_URL = os.getenv("CREATE_INWARD_API_URL", "http://localhost:8000/api/create_inward")
    CREATE_RTI_QUERY_API_URL = os.getenv("CREATE_RTI_QUERY_API_URL", "http://127.0.0.1:8000/api/v1/rti-queries")

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

class RedisConfig:
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
