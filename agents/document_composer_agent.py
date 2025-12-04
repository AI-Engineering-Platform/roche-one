# agents/document_composer_agent.py

from typing import Dict, Any
from openai import OpenAI

from config import (
    OPENAI_MODEL,
    CSR_TEMPLATE_PATH,
    GENERATED_CSR_PATH,
)
from utils.file_utils import read_docx_text, write_docx_text
from utils.logging_utils import setup_logger

logger = setup_logger("DocumentComposerAgent")
client = OpenAI()


def _call_llm(system_prompt: str, user_prompt: str) -> str:
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content


class DocumentComposerAgent:
    """
    Takes the extracted data from KnowledgeAgent and the CSR template,
    and generates a CSR document, written to GENERATED_CSR_PATH as a DOCX.
    """

    def __init__(self):
        self.template_path = CSR_TEMPLATE_PATH
        self.output_path = GENERATED_CSR_PATH

    def compose_document(self, extracted_data: Dict[str, Any]) -> str:
        logger.info("Reading CSR template...")
        template_text = read_docx_text(self.template_path)

        raw_sections = extracted_data.get("raw_extracted_sections", "")

        system_prompt = (
            "You are a medical writer generating a Clinical Study Report (CSR).\n"
            "You receive:\n"
            "- A CSR template with sections and structure.\n"
            "- Extracted content for each section (possibly in raw text form).\n\n"
            "Your job is to produce a clean, well-structured CSR document that "
            "follows the template headings and uses the extracted content where relevant."
        )

        user_prompt = (
            f"CSR Template:\n{template_text}\n\n"
            f"Extracted Section Content:\n{raw_sections}\n\n"
            "Using the template structure and extracted content, generate the final CSR text."
        )

        logger.info("Calling LLM from DocumentComposerAgent...")
        csr_text = _call_llm(system_prompt, user_prompt)

        logger.info(f"Writing generated CSR to: {self.output_path}")
        write_docx_text(self.output_path, csr_text)

        return self.output_path
