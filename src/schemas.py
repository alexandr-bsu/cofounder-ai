from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
import json


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class ConversationHistoryMessage(BaseModel):
    topic: str
    message: str
    role: str
    conversation_id: str
    profile_id: str


class Profile(BaseModel):
    id: str
    age: int = Field(default=0, gt=0)
    city: Optional[str] = Field(default=None)
    hiring_status: Optional[str] = Field(default=None)
    cofounder_skills: Optional[str] = Field(default=None)
    cofounder_experience: Optional[str] = Field(default=None)
    hiring_skills: Optional[str] = Field(default=None)
    cofounder_expertise: Optional[str] = Field(default=None)
    cofounder_income_expectations: Optional[str] = Field(default=None)
    cofounder_invest: Optional[str] = Field(default=None)
    cofounder_financial_needs: Optional[str] = Field(default=None)
    hours_per_day_project: Optional[str] = Field(default=None)
    cofounder_idea: Optional[str] = Field(default=None)
    participation_in_accelerators: Optional[str] = Field(default=None)
    telegram: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)

    @field_validator('cofounder_skills', 'hiring_skills', 'cofounder_expertise', mode='before')
    @classmethod
    def convert_array_to_string(cls, v):
        if isinstance(v, list):
            return '; '.join(str(item) for item in v)
        return v

class Tracker(BaseModel):
    data: Profile
    formName: str
    stage: str

class Transition(BaseModel):
    user_id: str
    code: str

class LLMRequest(BaseModel):
    prompt: Optional[str] = None
    topic: str
    profile_id: str
    
    @field_validator('prompt', mode='before')
    @classmethod
    def validate_prompt_json(cls, v):
        if isinstance(v, str):
            try:
                return json.dumps(json.loads(v))
            except (json.JSONDecodeError, TypeError):
                return json.dumps(v)
        return v 