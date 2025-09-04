from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
import json


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class LLMRequest(BaseModel):
    prompt: Optional[str] = None
    topic: str
    
    @field_validator('prompt', mode='before')
    @classmethod
    def validate_prompt_json(cls, v):
        if isinstance(v, str):
            try:
                return json.dumps(json.loads(v))
            except (json.JSONDecodeError, TypeError):
                return json.dumps(v)
        return v 