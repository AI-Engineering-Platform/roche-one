# agents/knowledge_agent.py

from typing import Dict, Any
from openai import OpenAI

from config import (
    OPENAI_MODEL,
    INPUT_DATA_JSON,
    CSR_TEMPLATE_PATH,
)
from utils.file_utils import read_json, read_docx_text
from utils.logging_utils import setup_logger

logger = setup_logger("KnowledgeAgent")

# Client reads OPENAI_API_KEY from environment / .env
client = OpenAI()


def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    Simple wrapper around OpenAI chat completions.
    Make sure OPENAI_MODEL is a chat-compatible model (e.g., gpt-4o-mini).
    """
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content


class KnowledgeAgent:
    """
    Reads clinical JSON + CSR template and extracts relevant information.
    For now it just returns raw text in a dict:
        {"raw_extracted_sections": <str>}
    """

    def __init__(self):
        self.data_path = INPUT_DATA_JSON
        self.template_path = CSR_TEMPLATE_PATH

    def extract_sections(self) -> Dict[str, Any]:
        logger.info("Reading clinical data JSON...")
        clinical_data = read_json(self.data_path)

        logger.info("Reading CSR template...")
        template_text = read_docx_text(self.template_path)

        system_prompt = (
            "You are a clinical documentation assistant.\n"
            "Using the clinical study data and CSR template, extract relevant content "
            "for all sections implied by the template. You may structure the answer "
            "by section headings, but you should return plain text."
        )

        user_prompt = (
            f"CSR Template:\n{template_text}\n\n"
            f"Clinical Study Data (JSON-like):\n{clinical_data}\n\n"
            "Extract and summarize the content for each section."
        )

        logger.info("Calling LLM from KnowledgeAgent...")
        result = _call_llm(system_prompt, user_prompt)

        return {"raw_extracted_sections": result}
