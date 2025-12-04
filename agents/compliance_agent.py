# agents/compliance_agent.py

from openai import OpenAI

from config import (
    OPENAI_MODEL,
    GENERATED_CSR_PATH,
    COMPLIANCE_REPORT_PATH,
)
from utils.file_utils import read_docx_text, write_docx_text
from utils.logging_utils import setup_logger

logger = setup_logger("ComplianceAgent")
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


ICH_E3_SECTION_CHECKLIST = [
    "Title Page",
    "Synopsis",
    "Table of Contents",
    "List of Abbreviations",
    "Ethics",
    "Study Administrative Structure",
    "Introduction",
    "Study Objectives",
    "Investigational Plan",
    "Study Patients",
    "Efficacy Evaluation",
    "Safety Evaluation",
    "Discussion and Overall Conclusions",
    "References",
    "Appendices",
]


class ComplianceAgent:
    """
    Evaluates the generated CSR against a simple ICH E3-style checklist
    and produces a compliance report in DOCX format.
    """

    def __init__(self):
        self.generated_csr_path = GENERATED_CSR_PATH
        self.output_path = COMPLIANCE_REPORT_PATH

    def check_regulatory_compliance(self) -> str:
        logger.info(f"Reading generated CSR from: {self.generated_csr_path}")
        csr_text = read_docx_text(self.generated_csr_path)

        checklist_str = "\n".join(f"- {s}" for s in ICH_E3_SECTION_CHECKLIST)

        system_prompt = (
            "You are a regulatory compliance expert.\n"
            "Evaluate a Clinical Study Report (CSR) against an ICH E3-style structure."
        )

        user_prompt = (
            f"ICH E3-Style Section Checklist:\n{checklist_str}\n\n"
            f"CSR Text:\n{csr_text}\n\n"
            "Produce a compliance report with:\n"
            "1) A section-by-section table in plain text with columns:\n"
            "   Section Name | Compliance Rating (Fully / Partial / Non-Compliant / Not Present) | Rationale\n"
            "2) An overall compliance summary (strengths, gaps, risks).\n"
            "3) A bullet list of actionable recommendations.\n"
            "Use ONLY plain text."
        )

        logger.info("Calling LLM from ComplianceAgent...")
        compliance_text = _call_llm(system_prompt, user_prompt)

        logger.info(f"Writing compliance report to: {self.output_path}")
        write_docx_text(self.output_path, compliance_text)

        return self.output_path
