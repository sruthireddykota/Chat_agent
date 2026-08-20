from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"  
    )

    REDIS_URL:str
    MCP_URL:str
    HUGGINGFACE_URL:str

    MONGODB_URI:str
    MONGODB_DB:str
    MONGODB_KM_DB:str
    MONGODB_USER_DB:str
    MONGODB_COLLECTION:str

    AZURE_DEPLOYMENT_NAME:str
    API_BASE_URL:str
    CODER_BASE_PATH:str
    
    EMBEDDING_MODEL:str

    QDRANT_HOST:str
    QDRANT_PORT:int

    #for deepeval
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_KEY: str
    OPENAI_API_VERSION: str

    AZURE_AI_PROJECT_ENDPOINT: str
    AZURE_TENANT_ID : str
    AZURE_CLIENT_ID : str
    AZURE_CLIENT_SECRET : str
    CODER_BASE_PATH: str 

    AZURE_DEPLOYMENT_NAME: str
    AZURE_OPENAI_DEPLOYMENT: str
    MAX_CONTEXT_WINDOW_TOKENS : int = 100000
    MAX_OUTPUT_TOKENS : int = 100000

    DOCLING_FILE_URL:str
    DOCLING_DOCUMENT_URL:str

    APPLICATION_INSIGHTS_CONNECTION_STR:str

    JWT_SECRET: str
    JWT_ISSUER: str = "chat-agent"
    JWT_EXPIRE_MINUTES: int = 60
    

settings = Settings()
