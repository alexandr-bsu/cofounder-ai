from openai import OpenAI
from mirascope.core import openai, BaseMessageParam, BaseDynamicConfig, Messages 
from src.config.settings import settings


class LLMService:
    def __init__(self):
        self.client: OpenAI = OpenAI(api_key=settings.openrouter.openrouter_api_key, base_url=settings.openrouter.base_url)

    async def infer(self, query, history: list[BaseMessageParam]=[]) -> BaseDynamicConfig:
        @openai.call(
            client=self.client,
            model=settings.openrouter.model_id,
            call_params={
                'reasoning_effort': 'medium',
                'max_tokens': 1800
            }
        )
        def _call() -> BaseDynamicConfig:
            messages: list[BaseMessageParam] = [
                *history,
                Messages.User(content=query),
            ]
            return {
                "messages": messages
            }
        
        return _call()


llm = LLMService()