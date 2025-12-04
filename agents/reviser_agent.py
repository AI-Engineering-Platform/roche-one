# agents/reviser_agent.py

from openai import OpenAI

from config import (
    OPENAI_MODEL,
    GENERATED_CSR_PATH,
    REVIEW_REPORT_PATH,
    COMPLIANCE_REPORT_PATH,
    REVISED_CSR_PATH,
)
from utils.file_utils import read_docx_text, write_docx_text
from utils.logging_utils import setup_logger

logger = setup_logger("ReviserAgent")
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


class ReviserAgent:
    """
    Uses the original CSR, review report, and compliance report to generate
    a revised CSR document.
    """

    def __init__(self):
        self.original_csr_path = GENERATED_CSR_PATH
        self.review_report_path = REVIEW_REPORT_PATH
        self.compliance_report_path = COMPLIANCE_REPORT_PATH
        self.output_path = REVISED_CSR_PATH

    def revise_document(self) -> str:
        logger.info(f"Reading original CSR from: {self.original_csr_path}")
        original_csr = read_docx_text(self.original_csr_path)

        logger.info(f"Reading review report from: {self.review_report_path}")
        review_text = read_docx_text(self.review_report_path)

        logger.info(f"Reading compliance report from: {self.compliance_report_path}")
        compliance_text = read_docx_text(self.compliance_report_path)

        system_prompt = (
            "You are a senior medical writer revising a Clinical Study Report (CSR).\n"
            "You receive:\n"
            "- The current CSR draft\n"
            "- A review report with completeness scores\n"
            "- A compliance report with regulatory alignment feedback\n\n"
            "Your job is to create a revised CSR that addresses the comments and "
            "improves structure, clarity, and compliance while NOT inventing any new data."
        )

        user_prompt = (
            f"Original CSR:\n{original_csr}\n\n"
            f"Review Report:\n{review_text}\n\n"
            f"Compliance Report:\n{compliance_text}\n\n"
            "Produce the full revised CSR text. Do not include extra commentary, "
            "only the revised CSR."
        )

        logger.info("Calling LLM from ReviserAgent...")
        revised_csr_text = _call_llm(system_prompt, user_prompt)

        logger.info(f"Writing revised CSR to: {self.output_path}")
        write_docx_text(self.output_path, revised_csr_text)

        return self.output_path
