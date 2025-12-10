# agents/knowledge_agent.py

import agents

from config import (
    INPUT_DATA_JSON,
    CSR_TEMPLATE_PATH,
    AGENT_LLM_NAMES,
)
from utils.file_utils import read_json, read_docx_text
from utils.logging_utils import setup_logger
from utils.agent_utils import async_openai_client


logger = setup_logger("KnowledgeAgent")


# Ideally, the supervisor would call this agent with the clinical study data
knowledge_agent = agents.Agent(
    name="KnowledgeAgent",
    instructions=f"""
You are a clinical documentation assistant.

Using the clinical study data and the CSR template, extract and organize 
relevant content for ALL sections implied by the template.

Return the output as well-structured plain text, clearly separated by
section headings (e.g., '1. Introduction', '2. Objectives', etc.).

Do NOT invent numerical results; if information is missing, write 'TBD'.

Extract and summarize the content for each section of the CSR,
following the template structure as much as possible.

CSR Template
------------
{read_docx_text(CSR_TEMPLATE_PATH)}

Clinical Study Data (JSON-like)
-------------------------------
{read_json(INPUT_DATA_JSON)}
""",
    tools=[],
    model=agents.OpenAIChatCompletionsModel(
        model=AGENT_LLM_NAMES["worker"], openai_client=async_openai_client
    ),
    output_type=str,
)
