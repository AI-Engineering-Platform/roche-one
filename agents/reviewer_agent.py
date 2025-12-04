# agents/reviewer_agent.py

from pathlib import Path
from openai import OpenAI

from config import (
    OPENAI_MODEL,
    GENERATED_CSR_PATH,
    CSR_SAMPLE_REPORT_PATH,
    REVIEW_REPORT_PATH,
)
from utils.file_utils import read_docx_text, read_pdf_text, write_docx_text
from utils.logging_utils import setup_logger

logger = setup_logger("ReviewerAgent")
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


class ReviewerAgent:
    """
    Compares the generated CSR with a sample CSR and produces a review report
    that includes section-wise completeness scoring and rationale.
    """

    def __init__(self):
        self.generated_csr_path = GENERATED_CSR_PATH
        self.sample_csr_path = CSR_SAMPLE_REPORT_PATH
        self.output_path = REVIEW_REPORT_PATH

    def review_document(self) -> str:
        logger.info(f"Reading generated CSR from: {self.generated_csr_path}")
        generated_text = read_docx_text(self.generated_csr_path)

        logger.info(f"Reading sample CSR from: {self.sample_csr_path}")
        sample_path = Path(self.sample_csr_path)
        if sample_path.suffix.lower() == ".pdf":
            sample_text = read_pdf_text(self.sample_csr_path)
        else:
            sample_text = read_docx_text(self.sample_csr_path)

        system_prompt = (
            "You are an expert clinical documentation reviewer.\n"
            "Compare a 'Generated CSR' with a 'Sample CSR' that is high-quality.\n"
            "Evaluate completeness and quality of each major section."
        )

        user_prompt = (
            f"Sample CSR (Reference):\n{sample_text}\n\n"
            f"Generated CSR (To Review):\n{generated_text}\n\n"
            "Create a review report with:\n"
            "1) A table-like section in plain text with columns:\n"
            "   Section Name | Completeness Score (0-100) | Rationale\n"
            "2) A short summary listing strong sections and sections needing improvement, "
            "with brief suggestions.\n"
            "Keep everything in plain text."
        )

        logger.info("Calling LLM from ReviewerAgent...")
        review_text = _call_llm(system_prompt, user_prompt)

        logger.info(f"Writing review report to: {self.output_path}")
        write_docx_text(self.output_path, review_text)

        return self.output_path
