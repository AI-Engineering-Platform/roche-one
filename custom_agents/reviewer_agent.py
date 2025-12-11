# agents/reviewer_agent.py

import agents
from agents import AgentOutputSchema

from config import AGENT_LLM_NAMES, CSR_SAMPLE_REPORT_PATH
from utils.agent_utils import async_openai_client
from utils.file_utils import read_pdf_text
from custom_agents.types import ReviewerContent


reviewer_agent = agents.Agent(
    name="ReviewerAgent",
    instructions=f"""
You are a clinical documentation reviewer. Evaluate the completeness of the Clinical Study Report (CSR) section by section.

Your output MUST contain:
1) A table listing each major CSR section and its completeness score (0–100).
2) A narrative rationale for each section score.
3) A summary of the main gaps.
4) An overall completeness score (0–100) on a separate line formatted EXACTLY as:
   OVERALL_COMPLETENESS_SCORE: <number>

Do not invent clinical results; only judge structure, clarity, and coverage.

Here's an example report, although it was generated from another template:

{read_pdf_text(CSR_SAMPLE_REPORT_PATH)}
""",
    tools=[],
    model=agents.OpenAIChatCompletionsModel(
        model=AGENT_LLM_NAMES["worker"],
        openai_client=async_openai_client
    ),
    output_type=AgentOutputSchema(ReviewerContent, strict_json_schema=False),
)

reviewer_tool = reviewer_agent.as_tool(
    tool_name="ReviewerTool",
    tool_description="This tool takes a CSR document as an input and produces a review report assessing its completeness.",
)
