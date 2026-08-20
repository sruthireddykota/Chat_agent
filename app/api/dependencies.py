from pydantic import BaseModel, Field

class SessionRequest(BaseModel):
    session_id :str = Field(description="User session ID")
    user_id : str = Field(description="User ID")
    
class SummarizeRequest(BaseModel):
    messages: list[dict]

class ReplaceSummaryRequest(BaseModel):
    summary: str
