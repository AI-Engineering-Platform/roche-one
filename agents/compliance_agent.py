# agents/compliance_agent.py

from typing import Tuple, Optional
import re

from config import (
    OPENAI_MODEL,
    GENERATED_CSR_PATH,
    COMPLIANCE_REPORT_PATH,
)
from utils.file_utils import read_docx_text, write_docx_text
from utils.logging_utils import setup_logger
from utils.agent_utils import create_chat

logger = setup_logger("ComplianceAgent")


def _parse_score_from_text(text: str) -> float:
    """
    Expect a line: OVERALL_COMPLIANCE_SCORE: <number>
    Returns 0.0 if not found.
    """
    match = re.search(r"OVERALL_COMPLIANCE_SCORE\s*:\s*(\d+)", text)
    if not match:
        logger.warning(
            "ComplianceAgent: No OVERALL_COMPLIANCE_SCORE found in compliance report, defaulting to 0."
        )
        return 0.0

    score = float(match.group(1))
    score = max(0.0, min(score, 100.0))
    return score


class ComplianceAgent:
    def __init__(self):
        self.csr_path = GENERATED_CSR_PATH
        self.output_path = COMPLIANCE_REPORT_PATH

    def check_regulatory_compliance(
        self,
        csr_path: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> Tuple[str, float]:
        """
        Check regulatory compliance and return:
          (compliance_report_path, compliance_score 0–100)

        csr_path: path to the CSR to assess
        output_path: where to save the compliance report (if None, uses config default)
        """
        if csr_path:
            self.csr_path = csr_path
        if output_path:
            self.output_path = output_path

        logger.info(f"[ComplianceAgent] Reading CSR for compliance check: {self.csr_path}")
        csr_text = read_docx_text(self.csr_path)

        system_prompt = (
            "You are a regulatory compliance expert evaluating a Clinical Study Report (CSR) "
            "against ICH E3 and common agency expectations.\n\n"
            "Your output MUST contain:\n"
            "1) Section-by-section assessment of regulatory compliance (compliant/partially/non-compliant).\n"
            "2) Rationale for each assessment.\n"
            "3) A summary of key deficiencies and recommended actions.\n"
            "4) An overall compliance score (0–100) on a separate line formatted EXACTLY as:\n"
            "   OVERALL_COMPLIANCE_SCORE: <number>\n"
            "Do not invent clinical results; only assess structure, content completeness, and regulatory expectations."
        )

        user_prompt = f"CSR TEXT:\n{csr_text}\n\nPlease perform the compliance review as requested."

        logger.info("[ComplianceAgent] Calling LLM for compliance check...")
        response = create_chat(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        compliance_text = response.choices[0].message.content

        score = _parse_score_from_text(compliance_text)
        logger.info(f"[ComplianceAgent] Parsed compliance score: {score}")

        logger.info(f"[ComplianceAgent] Writing compliance report to: {self.output_path}")
        write_docx_text(self.output_path, compliance_text)

        return self.output_path, score
