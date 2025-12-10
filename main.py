# main.py

import agents

from utils.logging_utils import setup_logger
from utils.file_utils import read_json

from langfuse import propagate_attributes
from utils.agent_utils import async_openai_client


from custom_agents.supervisor_agent import supervisor_agent

logger = setup_logger("MainPipeline")

from config import (
    CONFIDENCE_THRESHOLD,
    MAX_ITERATIONS,
    SESSION_ID,
    USER_ID,
    INPUT_DATA_JSON,
)




def _main():
    with propagate_attributes(
        user_id=USER_ID,
        session_id=SESSION_ID,
    ):
        logger.info(f"Running main CSR generation pipeline as User ID: {USER_ID}, Session ID: {SESSION_ID}")
        result = agents.Runner.run_sync(supervisor_agent,
                                   f"Create a CSR from the provided clinical study data with a confidence score of {CONFIDENCE_THRESHOLD} using a maximum number of iterations {MAX_ITERATIONS}:\n\n" +
                                   open(INPUT_DATA_JSON).read())
        
        return result

if __name__ == "__main__":
    result = _main()
    logger.info("Completed pipeline")
    logger.info(f"""Final Result
----------------
Initial Score: {result.initial_score}
Final Score: {result.final_score}
Iterations: {result.iterations}
Initial CSR Document: {result.initial_csr_document.filename}
Final CSR Document: {result.final_csr_document.filename}
""")
