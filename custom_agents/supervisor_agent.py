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

**IMPORTANT: You will receive clinical study data in the user message. Extract this data and pass it to the KnowledgeExtractionTool.**

Your tasks are to orchestrate the following steps:

1) **FIRST**: Extract the clinical study data from the user message and pass it to the KnowledgeExtractionTool.
   - The clinical study data will be provided as JSON-like text in the user message.
   - Call the KnowledgeExtractionTool with the full clinical study data as input.
   - This tool will return structured content organized by CSR section.

2) Use the DocumentComposerTool to generate an initial CSR draft (v0) from the extracted content returned by the KnowledgeExtractionTool.

3) Iteratively improve the CSR draft to reach the target confidence score:
   - Use the ReviewerTool to assess completeness of the current CSR.
   - Use the ComplianceTool to assess regulatory compliance with respect to ICH E3 guidelines.
   - Use the ReviserTool to revise the CSR based on feedback from the reviewer and compliance assessments.
   - Repeat this cycle until reaching the target confidence score or maximum iterations.

4) Return the final results including:
   - initial_csr_document: The first generated CSR
   - reviewer_report: Final completeness assessment
   - compliance_report: Final compliance assessment
   - final_csr_document: The final revised CSR
   - initial_score: The score of the initial CSR
   - final_score: The score of the final CSR
   - iterations: Number of revision cycles performed
""",
    tools=[knowledge_tool, composer_tool, reviewer_tool, compliance_tool, reviser_tool],
    model=agents.OpenAIChatCompletionsModel(
        model=AGENT_LLM_NAMES["supervisor"],
        openai_client=async_openai_client
    ),
    output_type=agents.AgentOutputSchema(SupervisorContent, strict_json_schema=False),
)