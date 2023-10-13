import json
from llm import LLM
from utils.bedrock import get_bedrock_client


class ClaudeV2(LLM):
    def generate_sql(self, prompt: str):
        bedrock_client = get_bedrock_client()

        final_prompt = f"\n\nHuman: {prompt}\n\nAssistant:"

        parameters = {
            "prompt": final_prompt,
            "max_tokens_to_sample": 600,
            "temperature": 0,
            "top_k": 10
        }

        invoke_model_kwargs = {
            "body": json.dumps(parameters),
            "accept": '*/*',
            "contentType": 'application/json',
            "modelId": 'anthropic.claude-v2'
        }

        res = bedrock_client.invoke_model(**invoke_model_kwargs)
        res_body = json.loads(res.get('body').read())
        query = res_body['completion'].replace("SQLQuery:", "").strip()
        return query
