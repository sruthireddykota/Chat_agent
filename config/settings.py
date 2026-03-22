from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    REDIS_URL:str
    MCP_URL:str

    MONGODB_URI:str
    MONGODB_DB:str
    MONGODB_KM_DB:str
    MONGODB_USER_DB:str
    MONGODB_COLLECTION:str

    AZURE_DEPLOYMENT_NAME:str
    API_BASE_URL:str
    
    EMBEDDING_MODEL:str

    QDRANT_HOST:str
    QDRANT_PORT:int

    #for deepeval
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_KEY: str
    OPENAI_API_VERSION: str
    AZURE_DEPLOYMENT_NAME: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()


