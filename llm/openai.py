from langchain import llms

from llm import LLM


class OpenAI(LLM):
    def generate_sql(self, prompt: str):
        openai_client = llms.OpenAI()
        query = openai_client.predict(prompt).replace("SQLQuery:", "").strip()
        return query
