from openai import AzureOpenAI
from dotenv import load_dotenv
import os
load_dotenv()

def get_embedding_client():
    client=AzureOpenAI(
        api_key=os.getenv("EMBEDDING_API_KEY"),
        azure_endpoint=os.getenv("EMBEDDING_ENDPOINT"),
        api_version="2024-02-15-preview"
    )
    return client