from openai import OpenAI
from mirascope.core import openai, BaseMessageParam, BaseDynamicConfig, Messages
from src.config.settings import settings
from mirascope.integrations.langfuse import with_langfuse

import os
os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse.langfuse_public_key
os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse.langfuse_secret_key
os.environ["LANGFUSE_HOST"] = settings.langfuse.langfuse_host

class LLMService:
    def __init__(self):
        self.client: OpenAI = OpenAI(
            api_key=settings.openrouter.openrouter_api_key, base_url=settings.openrouter.base_url)

    async def infer(self, query, history: list[BaseMessageParam] = [], session_id: str=None) -> BaseDynamicConfig:
        @with_langfuse()
        @openai.call(
            client=self.client,
            model=settings.openrouter.model_id,
            call_params={
                'reasoning_effort': 'high',
                'max_tokens': 1800*3
            }
        )
        def _call() -> BaseDynamicConfig:
            messages: list[BaseMessageParam] = [
                *history,
            ]
            # Only add user message if query is not None or empty
            if query:
                messages.append(Messages.User(content=query))

            override_settings = {
                "messages": messages
            }

            if session_id is not None:
               override_settings['langfuse_session_id'] = session_id 

            return override_settings

        return _call()


llm = LLMService()
