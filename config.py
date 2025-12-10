import os
import secrets
from dotenv import load_dotenv

load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL")
OPENAI_API_KEY= os.getenv("OPENAI_API_KEY")
INPUT_DATA_JSON = os.getenv("INPUT_DATA_JSON")
CSR_TEMPLATE_PATH = os.getenv("CSR_TEMPLATE_PATH")
CSR_SAMPLE_REPORT_PATH = os.getenv("CSR_SAMPLE_REPORT_PATH")
GENERATED_CSR_PATH = os.getenv("GENERATED_CSR_PATH")
REVIEW_REPORT_PATH = os.getenv("REVIEW_REPORT_PATH")
COMPLIANCE_REPORT_PATH = os.getenv("COMPLIANCE_REPORT_PATH")
REVISED_CSR_PATH = os.getenv("REVISED_CSR_PATH")
CONFIDENCE_THRESHOLD=os.getenv("CONFIDENCE_THRESHOLD")
MAX_ITERATIONS=os.getenv("MAX_ITERATIONS")

SESSION_ID = os.getenv("SESSION_ID", f"session_{secrets.token_hex(3)}")
USER_ID = os.getenv("USER_ID", "default_user")

AGENT_LLM_NAMES = {
    "worker": OPENAI_MODEL,  # less expensive,
    "supervisor": OPENAI_MODEL,  # more expensive, better at reasoning and planning
}