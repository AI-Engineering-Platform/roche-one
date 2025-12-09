# agents/reviewer_agent.py

from typing import Tuple, Optional
import re

from openai import OpenAI as RawOpenAI           # for Gemini-compatible endpoint
from langfuse.openai import OpenAI as LFOpenAI   # default OpenAI with Langfuse

from config import (
    OPENAI_MODEL,
    GENERATED_CSR_PATH,
    REVIEW_REPORT_PATH,
    GEMINI_API_BASE,
    GEMINI_API_KEY,
    GEMINI_MODEL
    )
from utils.file_utils import read_docx_text, write_docx_text
from utils.logging_utils import setup_logger

logger = setup_logger("ReviewerAgent")


def _get_client():
    """
    Returns an OpenAI-compatible client.
    If GEMINI_API_BASE and GEMINI_API_KEY are set, use that endpoint (Gemini gateway).
    Otherwise, fall back to the standard Langfuse-wrapped OpenAI client.
    """
    if GEMINI_API_BASE and GEMINI_API_KEY:
        logger.info(
            f"[ReviewerAgent] Using Gemini-compatible OpenAI endpoint at {GEMINI_API_BASE}"
        )
        return RawOpenAI(
            base_url=GEMINI_API_BASE,
            api_key=GEMINI_API_KEY,
        )
    else:
        logger.info("[ReviewerAgent] Using default OpenAI client (Langfuse-wrapped).")
        return LFOpenAI()


def _parse_score_from_text(text: str) -> float:
    """
    Expect the LLM to include a line like:
      OVERALL_COMPLETENESS_SCORE: <number>
    Returns 0.0 if not found.
    """
    match = re.search(r"OVERALL_COMPLETENESS_SCORE\s*:\s*(\d+)", text)
    if not match:
        logger.warning(
            "ReviewerAgent: No OVERALL_COMPLETENESS_SCORE found in review report, defaulting to 0."
        )
        return 0.0

    score = float(match.group(1))
    score = max(0.0, min(score, 100.0))
    return score


class ReviewerAgent:

    def __init__(self):
        self.csr_path = GENERATED_CSR_PATH
        self.output_path = REVIEW_REPORT_PATH
        self.client = _get_client()

    def review_document(
        self,
        csr_path: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> Tuple[str, float]:
        """
        Review the CSR and return:
          (review_report_path, completeness_score 0–100)

        csr_path: path to the CSR to review
        output_path: where to save the review report (if None, uses config default)
        """
        if csr_path:
            self.csr_path = csr_path
        if output_path:
            self.output_path = output_path

        logger.info(f"[ReviewerAgent] Reading CSR for review: {self.csr_path}")
        csr_text = read_docx_text(self.csr_path)

        system_prompt = (
            "You are a clinical documentation reviewer. Evaluate the completeness of "
            "the Clinical Study Report (CSR) section by section.\n\n"
            "Your output MUST contain:\n"
            "1) A table listing each major CSR section and its completeness score (0–100).\n"
            "2) A narrative rationale for each section score.\n"
            "3) A summary of the main gaps.\n"
            "4) An overall completeness score (0–100) on a separate line formatted EXACTLY as:\n"
            "   OVERALL_COMPLETENESS_SCORE: <number>\n"
            "Do not invent clinical results; only judge structure, clarity, and coverage."
        )

        user_prompt = f"CSR TEXT:\n{csr_text}\n\nPlease perform the completeness review as requested."

        logger.info("[ReviewerAgent] Calling LLM for completeness review...")
        response = self.client.chat.completions.create(
            model=GEMINI_MODEL if (GEMINI_API_BASE and GEMINI_API_KEY) else OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        review_text = response.choices[0].message.content

        score = _parse_score_from_text(review_text)
        logger.info(f"[ReviewerAgent] Parsed completeness score: {score}")

        logger.info(f"[ReviewerAgent] Writing review report to: {self.output_path}")
        write_docx_text(self.output_path, review_text)

        return self.output_path, score
