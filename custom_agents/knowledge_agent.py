# agents/knowledge_agent.py

import agents

from config import (
    CSR_TEMPLATE_PATH,
    AGENT_LLM_NAMES,
)
from utils.file_utils import read_docx_text
from utils.agent_utils import async_openai_client
from custom_agents.types import KnowledgeContent


knowledge_agent = agents.Agent(
    name="KnowledgeAgent",
    instructions=f"""
You are a clinical documentation assistant.

You are provided clinical study data in JSON format.

Using the clinical study data and the CSR template (below), extract and organize 
relevant content for ALL sections implied by the template.

Return the output as well-structured plain text, clearly separated by
section headings (e.g., '1. Introduction', '2. Objectives', etc.).

Do NOT invent numerical results; if information is missing, write 'TBD'.

Extract and summarize the content for each section of the CSR,
following the template structure as much as possible.

CSR Template
------------
{read_docx_text(CSR_TEMPLATE_PATH)}
""",
    tools=[],
    model=agents.OpenAIChatCompletionsModel(
        model=AGENT_LLM_NAMES["worker"],
        openai_client=async_openai_client
    ),
    output_type=KnowledgeContent,
)

knowledge_tool = knowledge_agent.as_tool(
    tool_name="KnowledgeExtractionTool",
    tool_description="This tool takes a clinical study data (json-like) and returns content for each section of the CSR",
)