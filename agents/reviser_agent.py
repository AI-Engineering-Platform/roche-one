# agents/reviser_agent.py

from typing import Optional

from config import (
    OPENAI_MODEL,
    GENERATED_CSR_PATH,
    REVIEW_REPORT_PATH,
    COMPLIANCE_REPORT_PATH,
    REVISED_CSR_PATH,
)
from utils.file_utils import read_docx_text, write_docx_text
from utils.logging_utils import setup_logger
from utils.agent_utils import create_chat

logger = setup_logger("ReviserAgent")


class ReviserAgent:
    """
    Takes the current CSR + review report + compliance report,
    and produces an improved CSR.
    """

    def __init__(self):
        self.csr_path = GENERATED_CSR_PATH
        self.review_path = REVIEW_REPORT_PATH
        self.compliance_path = COMPLIANCE_REPORT_PATH
        self.output_path = REVISED_CSR_PATH

    def revise_document(
        self,
        csr_path: Optional[str] = None,
        review_path: Optional[str] = None,
        compliance_path: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Revise the CSR and write to output_path (or config default if not provided).
        Returns the path to the revised CSR.
        """
        if csr_path:
            self.csr_path = csr_path
        if review_path:
            self.review_path = review_path
        if compliance_path:
            self.compliance_path = compliance_path
        if output_path:
            self.output_path = output_path

        logger.info("[ReviserAgent] Reading CSR, review report, and compliance report...")
        csr_text = read_docx_text(self.csr_path)
        review_text = read_docx_text(self.review_path)
        compliance_text = read_docx_text(self.compliance_path)

        system_prompt = (
            "You are a senior medical writer tasked with revising a Clinical Study Report (CSR) "
            "based on feedback from:\n"
            "- A completeness review report\n"
            "- A regulatory compliance report\n\n"
            "Your goal is to generate an improved version of the CSR that:\n"
            "Ensure you follow the table of contents of the orginal CSR with the same numbering and header names For e.g. 3.1.2 Changes in Study Conduct, do not alter the numbering or header text or include any special characters like *\n"
            "- Addresses completeness gaps\n"
            "- Addresses regulatory compliance issues\n"
            "- Improves clarity and structure\n\n"
            "- Retains and populates all sections and data from the original CSR that are not not available in the new CSR "
            "Do NOT invent new numerical results or patients; refine only the narrative, structure, and coverage."
        )

        user_prompt = (
            f"CURRENT CSR:\n{csr_text}\n\n"
            f"COMPLETENESS REVIEW REPORT:\n{review_text}\n\n"
            f"COMPLIANCE REPORT:\n{compliance_text}\n\n"
            "Please produce an improved CSR version that addresses the identified issues."
        )

        logger.info("[ReviserAgent] Calling LLM to revise CSR...")
        response = create_chat(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        revised_text = response.choices[0].message.content

        logger.info(f"[ReviserAgent] Writing revised CSR to: {self.output_path}")
        write_docx_text(self.output_path, revised_text)

        return self.output_path
