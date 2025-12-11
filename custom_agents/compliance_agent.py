# agents/compliance_agent.py

import agents
from agents import AgentOutputSchema

from config import AGENT_LLM_NAMES
from utils.agent_utils import async_openai_client
from utils.file_utils import read_pdf_text
from custom_agents.types import ReviewerContent


compliance_agent = agents.Agent(
    name="ComplianceAgent",
    instructions=f"""
You are a regulatory compliance expert evaluating a Clinical Study Report (CSR) against ICH E3 and common agency expectations.

Your output MUST contain:
1) Section-by-section assessment of regulatory compliance (compliant/partially/non-compliant).
2) Rationale for each assessment.
3) A summary of key deficiencies and recommended actions.
4) An overall compliance score (0–100) on a separate line formatted EXACTLY as:
   OVERALL_COMPLIANCE_SCORE: <number>

Do not invent clinical results; only assess structure, content completeness, and regulatory expectations.

The ICH guidelines are included below:

{read_pdf_text("data/input/E3_Guideline.pdf")}
""",
    tools=[],
    model=agents.OpenAIChatCompletionsModel(
        model=AGENT_LLM_NAMES["worker"],
        openai_client=async_openai_client
    ),
    output_type=AgentOutputSchema(ReviewerContent, strict_json_schema=False),
)

compliance_tool = compliance_agent.as_tool(
    tool_name="ComplianceTool",
    tool_description="This tool takes a CSR document as an input and produces a review report assessing its compliance with ICH requirements.",
)
