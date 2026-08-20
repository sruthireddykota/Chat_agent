from pydantic import BaseModel, Field, field_validator

from app.models.constants import (Role,AgentType)

class QueryRequest(BaseModel):
    text: str = Field(description="")
    files:list = Field(description="", default_factory=list)

class AgentRequest(BaseModel):
    query: QueryRequest 
    session_id: str = Field(description="User Session ID")
    user_id : str = Field(description="User ID")
    agent_name: AgentType = Field(default=AgentType.GENERIC)

    @field_validator("agent_name", mode="before")
    @classmethod
    def normalize_agent_name(cls, value):
        if isinstance(value, str):
            return value.strip().lower()
        return value
