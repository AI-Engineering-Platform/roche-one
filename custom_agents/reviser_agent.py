# agents/reviser_agent.py

import agents

from config import AGENT_LLM_NAMES
from utils.agent_utils import async_openai_client
from custom_agents.types import CsrDocument


reviser_agent = agents.Agent(
    name="ReviserAgent",
    instructions=f"""
You are a senior medical writer tasked with revising a Clinical Study Report (CSR) based on feedback from:
- A completeness review report
- A regulatory compliance report

Your goal is to generate an improved version of the CSR that:
- Addresses completeness gaps
- Addresses regulatory compliance issues
- Improves clarity and structure
- Retains all sections and data from the original CSR that are not flagged as needing changeDo NOT invent new numerical results or patients; refine only the narrative, structure, and coverage.

The output nct_id should be the same as the input file, but the version number should be incremented by 1. The output should also contain the revised markdown content
""",
    tools=[],
    model=agents.OpenAIChatCompletionsModel(
        model=AGENT_LLM_NAMES["worker"],
        openai_client=async_openai_client
    ),
    output_type=CsrDocument,
)

reviser_tool = reviser_agent.as_tool(
    tool_name="ReviserTool",
    tool_description="This tool takes a CSR document, a completeness review report, and a compliance report as inputs and produces a revised CSR document that addresses the identified issues.",
)
