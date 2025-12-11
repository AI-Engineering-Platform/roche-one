from openinference.instrumentation.openai_agents import OpenAIAgentsInstrumentor
from langfuse.openai import AsyncOpenAI, OpenAI
from langfuse import get_client
from config import OPENAI_API_KEY

OpenAIAgentsInstrumentor().instrument()

langfuse_client = get_client()

openai_client = OpenAI(api_key=OPENAI_API_KEY)
async_openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
