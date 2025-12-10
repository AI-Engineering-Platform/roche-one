# agents/reviser_agent.py

import agents

from config import AGENT_LLM_NAMES
from utils.agent_utils import async_openai_client
from custom_agents.types import SupervisorContent
from custom_agents.knowledge_agent import knowledge_tool
from custom_agents.document_composer_agent import composer_tool
from custom_agents.reviewer_agent import reviewer_tool
from custom_agents.compliance_agent import compliance_tool
from custom_agents.reviser_agent import reviser_tool


supervisor_agent = agents.Agent(
    name="SupervisorAgent",
    instructions="""
You are the supervisor agent coordinating the CSR generation pipeline.

Your tasks are to orchestrate the following steps:
1) Use the KnowledgeExtractionTool to extract structured content from clinical study data.
2) Use the DocumentComposerTool to generate an initial CSR draft (v0) from the extracted content.
3) Iteratively improve the CSR draft to a target score, which involves:
   - Running the ReviewerAgent to assess completeness.
   - Running the ComplianceAgent to assess regulatory compliance.
   - Running the ReviserAgent to revise the CSR based on feedback.
""",
    tools=[knowledge_tool, composer_tool, reviewer_tool, compliance_tool, reviser_tool],
    model=agents.OpenAIChatCompletionsModel(
        model=AGENT_LLM_NAMES["supervisor"],
        openai_client=async_openai_client
    ),
    output_type=agents.AgentOutputSchema(SupervisorContent, strict_json_schema=False),
)