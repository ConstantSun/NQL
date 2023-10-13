import os

from llm import LLM
from llm.claudev2 import ClaudeV2
from llm.openai import OpenAI


def get_llm_client() -> LLM:
    llm = os.getenv("LLM")

    llm_dict = {
        "openai": OpenAI(),
        "claude-v2": ClaudeV2()
    }

    client = llm_dict.get(llm)

    if client is None:
        raise Exception(f"Model: {llm} not found.")

    return client