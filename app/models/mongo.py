from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
from app.models.constants import (Role,AgentType)

def _time_now():
    return datetime.now(timezone.utc)

class MongoStoreMessage(BaseModel):
    session_id:str = Field(description = "User chat session ID")
    role : Role = Field(description="role",default_factory=Role.USER)
    content : str = Field(description="Response")
    timestamp : datetime = Field(description="Timestamp of storing",default_factory=_time_now)
    sources : str = Field(description="Source")
    agent_name : AgentType = Field(description="Agent name",default_factory=AgentType)
    user_id : str = Field(description=" User ID")

class MongoDocumentData(BaseModel):
    document_name: str = Field(description="Documnet name")
    document_id : str = Field(description="Document id")
    document_type : str = Field(description="Document type")
    timestamp : datetime = Field(default_factory=_time_now)
    chunk_count : int = Field(description="No of chunks")
    uploaded_by : str = Field(description="Uploaded user name")
    tags : Optional[list] = Field(description="tags",default_factory=list)

class MongoUser(BaseModel):
    
    username:str = Field(description="User name")
    user_id : str = Field(description="User Id")
    password : str = Field(description="User password")
    email_id : str = Field(description="User email id")
    created_at : datetime = Field(default_factory=_time_now)
    logged_in : bool = Field(description="Logged in ")
    last_logged_in : datetime = Field(default_factory=_time_now)

class UserDetails(BaseModel):
    
    username : str = Field(description="User name")
    password : str = Field(description="user password")
    user_id : str = Field(description="User id")
    email_id : str =Field(description="User email id")
    logged_in : datetime = Field(default_factory=_time_now)

class LoginRequest(BaseModel):
    email_id : str = Field(description = "User email id")
    password : str = Field(description = "User Password")