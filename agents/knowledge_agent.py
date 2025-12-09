# agents/knowledge_agent.py
from typing import Dict, Any

import agents

from config import (
    INPUT_DATA_JSON,
    CSR_TEMPLATE_PATH,
    AGENT_LLM_NAMES,
)
from utils.file_utils import read_json, read_docx_text
from utils.logging_utils import setup_logger
from utils.agent_utils import async_openai_client
from types import CsrDocument


logger = setup_logger("KnowledgeAgent")

knowledge_agent = agents.Agent(
    name="KnowledgeAgent",
    instructions=(
        "You are a clinical documentation assistant.\n"
        "Using the clinical study data and the CSR template, extract and organize "
        "relevant content for ALL sections implied by the template.\n\n"
        "Return the output as well-structured plain text, clearly separated by "
        "section headings (e.g., '1. Introduction', '2. Objectives', etc.).\n"
        "Do NOT invent numerical results; if information is missing, write 'TBD'.\n\n"
        f"CSR Template:\n{read_docx_text(CSR_TEMPLATE_PATH)}\n\n"
        f"Clinical Study Data (JSON-like):\n{read_json(INPUT_DATA_JSON)}\n\n"
        "Extract and summarize the content for each section of the CSR, "
        "following the template structure as much as possible."
    ),
    tools=[],
    model=agents.OpenAIChatCompletionsModel(
        model=AGENT_LLM_NAMES["worker"], openai_client=async_openai_client
    ),
    output_type=CsrDocument,
)
