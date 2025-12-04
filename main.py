# main.py

from agents.knowledge_agent import KnowledgeAgent
from agents.document_composer_agent import DocumentComposerAgent
from agents.reviewer_agent import ReviewerAgent
from agents.compliance_agent import ComplianceAgent
from agents.reviser_agent import ReviserAgent
from utils.logging_utils import setup_logger

logger = setup_logger("Main")


def run_pipeline():
    logger.info("Starting CSR multi-agent pipeline (chat.completions)...")

    # 1) Knowledge Agent
    knowledge_agent = KnowledgeAgent()
    extracted_sections = knowledge_agent.extract_sections()
    logger.info("KnowledgeAgent finished extraction.")

    # 2) Document Composer Agent
    composer_agent = DocumentComposerAgent()
    generated_csr_path = composer_agent.compose_document(extracted_sections)
    logger.info(f"DocumentComposerAgent generated CSR at: {generated_csr_path}")

    # 3) Reviewer Agent
    reviewer_agent = ReviewerAgent()
    review_report_path = reviewer_agent.review_document()
    logger.info(f"ReviewerAgent created review report at: {review_report_path}")

    # 4) Compliance Agent
    compliance_agent = ComplianceAgent()
    compliance_report_path = compliance_agent.check_regulatory_compliance()
    logger.info(f"ComplianceAgent created compliance report at: {compliance_report_path}")

    # 5) Reviser Agent
    reviser_agent = ReviserAgent()
    revised_csr_path = reviser_agent.revise_document()
    logger.info(f"ReviserAgent created revised CSR at: {revised_csr_path}")

    logger.info("Pipeline completed successfully.")


if __name__ == "__main__":
    run_pipeline()
