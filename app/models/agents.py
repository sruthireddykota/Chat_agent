from pydantic import BaseModel, Field

from app.models.constants import (Role,AgentType)

class QueryRequest(BaseModel):
    text: str = Field(description="")
    files:list = Field(description="", default_factory=list)

class AgentRequest(BaseModel):
    query: QueryRequest 
    session_id: str = Field(description="User Session ID")
    user_id : str = Field(description="User ID")


class AgentRunRequest(AgentRequest):
    agent_name: AgentType = Field(default=AgentType.GENERIC)


