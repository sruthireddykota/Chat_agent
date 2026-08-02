from pydantic import BaseModel, Field

class SessionRequest(BaseModel):
    session_id :str = Field(description="User session ID")
    user_id : str = Field(description="User ID")
    

from functools import lru_cache
from app.repositeries.mongodb_server import MongoStore


@lru_cache
def get_mongo_store() -> MongoStore:
    """Cached singleton MongoStore instance, injected into routes via Depends."""
    return MongoStore()
