# agents/knowledge_agent.py
from typing import Dict, Any

from config import (
    OPENAI_MODEL,
    INPUT_DATA_JSON,
    CSR_TEMPLATE_PATH,
)
from utils.file_utils import read_json, read_docx_text
from utils.logging_utils import setup_logger
from utils.agent_utils import create_chat

logger = setup_logger("KnowledgeAgent")


def _call_llm(system_prompt: str, user_prompt: str) -> str:
    logger.info("[KnowledgeAgent] Calling OpenAI (Langfuse-wrapped)")

    response = create_chat(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content
    logger.info("[KnowledgeAgent] LLM call successful.")
    return content


class KnowledgeAgent:

    def __init__(self):
        self.data_path = INPUT_DATA_JSON
        self.template_path = CSR_TEMPLATE_PATH

    def extract_sections(self) -> Dict[str, Any]:
        logger.info("Reading clinical data JSON...")
        clinical_data = read_json(self.data_path)

        logger.info("Reading CSR template DOCX...")
        template_text = read_docx_text(self.template_path)

        system_prompt = (
            "You are a clinical documentation assistant.\n"
            "Using the clinical study data and the CSR template, extract and organize "
            "relevant content for ALL sections implied by the template.\n\n"
            "Return the output as well-structured plain text, clearly separated by "
            "section headings (e.g., '1. Introduction', '2. Objectives', etc.).\n"
            "Do NOT invent numerical results; if information is missing, write 'TBD'."
        )

        user_prompt = (
            f"CSR Template:\n{template_text}\n\n"
            f"Clinical Study Data (JSON-like):\n{clinical_data}\n\n"
            "Extract and summarize the content for each section of the CSR, "
            "following the template structure as much as possible."
        )

        logger.info("Calling LLM from KnowledgeAgent...")
        result_text = _call_llm(system_prompt, user_prompt)

        return {"raw_extracted_sections": result_text}
