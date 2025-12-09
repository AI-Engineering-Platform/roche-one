from langfuse.openai import OpenAI
from langfuse import propagate_attributes

from config import SESSION_ID, USER_ID

client = OpenAI()


def create_chat(
    model: str,
    messages: list[dict],
    **kwargs,
) -> "OpenAI.chat.completions.CreateResponse":
    """
    Wrapper around Langfuse-wrapped OpenAI client to execute chat completions
    with the given model and messages.
    Additional kwargs are passed to the create() method.
    """
    with propagate_attributes(
        user_id=USER_ID,
        session_id=SESSION_ID,
    ):
        return client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs,
        )
