# main.py

import agents

from pathlib import Path

from utils.logging_utils import setup_logger
from utils.file_utils import read_json

from langfuse import propagate_attributes
from utils.agent_utils import async_openai_client

from custom_agents.knowledge_agent import knowledge_tool
from custom_agents.document_composer_agent import composer_tool

logger = setup_logger("MainPipeline")

from config import (
    CONFIDENCE_THRESHOLD,
    MAX_ITERATIONS,
    SESSION_ID,
    USER_ID,
    AGENT_LLM_NAMES,
    INPUT_DATA_JSON,
)
def improve_csr_until_confident(
    initial_csr_path: str,
    target_score: float = CONFIDENCE_THRESHOLD,
    max_iterations: int = MAX_ITERATIONS,
):
    """
    Run Reviewer + Compliance + Reviser in a loop until the
    combined score reaches target_score or we hit max_iterations.

    Combined score = average of reviewer & compliance scores (0–100).

    Filenames:
      - initial_csr_path is treated as v0
      - Iteration i (1..N):
          CSR:        <stem>_v{i}.docx
          Review:     <stem>_review_v{i}.docx
          Compliance: <stem>_compliance_v{i}.docx
    """

    reviewer = ReviewerAgent()
    compliance = ComplianceAgent()
    reviser = ReviserAgent()

    # Base path info
    csr_base = Path(initial_csr_path)
    csr_dir = csr_base.parent
    csr_stem = csr_base.stem  # e.g. "generated_csr"

    current_csr_path = initial_csr_path
    final_score = 0.0
    review_report_path = ""
    compliance_report_path = ""
    iterations_done = 0

    for iteration in range(1, max_iterations + 1):
        iterations_done = iteration
        logger.info(f"========== Improvement iteration {iteration} ==========")

        # Construct versioned filenames for this iteration
        iter_csr_path = str(csr_dir / f"{csr_stem}_v{iteration}.docx")
        iter_review_path = str(csr_dir / f"{csr_stem}_review_v{iteration}.docx")
        iter_compliance_path = str(csr_dir / f"{csr_stem}_compliance_v{iteration}.docx")

        # 1) Reviewer
        review_report_path, review_score = reviewer.review_document(
            csr_path=current_csr_path,
            output_path=iter_review_path,
        )
        logger.info(f"[Iteration {iteration}] ReviewerAgent score: {review_score}")

        # 2) Compliance
        compliance_report_path, compliance_score = compliance.check_regulatory_compliance(
            csr_path=current_csr_path,
            output_path=iter_compliance_path,
        )
        logger.info(f"[Iteration {iteration}] ComplianceAgent score: {compliance_score}")

        # 3) Combined confidence score
        final_score = (review_score + compliance_score) / 2.0
        logger.info(f"[Iteration {iteration}] Combined confidence score: {final_score}")

        if final_score >= target_score:
            logger.info(
                f"Target score {target_score} reached at iteration {iteration}. "
                f"Stopping improvement loop."
            )
            # We treat the CSR used in this iteration as the final one
            final_csr_path = current_csr_path
            break

        # 4) Reviser – improve CSR using latest review & compliance
        logger.info(
            f"[Iteration {iteration}] Score below target ({target_score}), invoking ReviserAgent..."
        )
        current_csr_path = reviser.revise_document(
            csr_path=current_csr_path,
            review_path=review_report_path,
            compliance_path=compliance_report_path,
            output_path=iter_csr_path,
        )

    else:
        # If loop ends without break (score never reached target)
        final_csr_path = current_csr_path

    logger.info(
        f"Improvement loop finished. Final score: {final_score}, "
        f"iterations: {iterations_done} (target: {target_score})."
    )

    return {
        "final_csr_path": final_csr_path,
        "review_report_path": review_report_path,
        "compliance_report_path": compliance_report_path,
        "final_score": final_score,
        "iterations": iterations_done,
    }


main_agent = agents.Agent(
    name="SupervisorAgent",
    instructions="""
You are the supervisor agent coordinating the CSR generation pipeline.

Your tasks are to orchestrate the following steps:
1) Use the KnowledgeExtractionTool to extract structured content from clinical study data.
2) Use the DocumentComposerTool to generate an initial CSR draft (v0) from the extracted content.
""",
    tools=[knowledge_tool, composer_tool],
    model=agents.OpenAIChatCompletionsModel(
        model=AGENT_LLM_NAMES["supervisor"],
        openai_client=async_openai_client
    ),
)

def _main():
    with propagate_attributes(
        user_id=USER_ID,
        session_id=SESSION_ID,
    ):
        logger.info(f"Running main CSR generation pipeline as User ID: {USER_ID}, Session ID: {SESSION_ID}")
        result = agents.Runner.run_sync(main_agent,
                                   "Create a CSR from the provided clinical study data:\n\n" +
                                   open(INPUT_DATA_JSON).read())
        
        return result

if __name__ == "__main__":
    result = _main()
    logger.info(result)
