from openai import AzureOpenAI
from config.settings import settings
import os 

def get_embedding_client():
    client=AzureOpenAI(
        api_key=os.getenv("EMBEDDING_API_KEY"),
        azure_endpoint=os.getenv("EMBEDDING_ENDPOINT"),
        api_version="2024-02-15-preview"
    )
    return client

client=get_embedding_client()

def query_embedding(query):
    response=client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=query
    )
    return response.data[0].embedding