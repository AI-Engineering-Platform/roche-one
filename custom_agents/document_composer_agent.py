# agents/document_composer_agent.py

import agents

from config import (
    CSR_TEMPLATE_PATH,
    AGENT_LLM_NAMES,
)
from custom_agents.types import CsrDocument
from utils.file_utils import read_docx_text
from utils.agent_utils import async_openai_client


composer_agent = agents.Agent(
    name="ComposerAgent",
    instructions=f"""
You are a medical writer generating a Clinical Study Report (CSR).

You receive structured content (either markdown or plain text) extracted from clinical study data as an input.

Using the template provided below, you will compose a well-structured CSR document. Ensure you follow the template structure strictly.

Your job is to produce a clean, well-structured CSR document that follows the template headings and uses the extracted content where relevant.

The document filename should be "CSR_<nct_id>_v0.docx", where <nct_id> is the NCT ID extracted from the clinical study data.

CSR Template
------------
{read_docx_text(CSR_TEMPLATE_PATH)}
""",
    tools=[],
    model=agents.OpenAIChatCompletionsModel(
        model=AGENT_LLM_NAMES["worker"],
        openai_client=async_openai_client
    ),
    output_type=CsrDocument,
)

composer_tool = composer_agent.as_tool(
    tool_name="DocumentComposerTool",
    tool_description="This tool takes structured content (markdown or plain text) and generates a Clinical Study"
)
