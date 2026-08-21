from __future__ import annotations

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from typing import Iterable
import os
from pathlib import Path
from dotenv import load_dotenv

# import variables from .env
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

client = OpenAI(
    api_key=os.getenv("PARLEY_API_KEY"),
    base_url="https://parley.api.mit.edu/v1"
)

# create chat Completion endpoint
def parleyChatCompletion(messages: Iterable[ChatCompletionMessageParam], model="bedrock/claude-haiku-4-5", temperature=0.7, max_tokens=500) -> str|None:
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content