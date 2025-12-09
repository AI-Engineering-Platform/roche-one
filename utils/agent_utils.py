from langfuse.openai import OpenAI
from langfuse import Langfuse

from config import SESSION_ID, USER_ID

# Initialize Langfuse with context
langfuse = Langfuse()
langfuse.set_state_property("user_id", USER_ID)
langfuse.set_state_property("session_id", SESSION_ID)

# Then use client normally
client = OpenAI()
