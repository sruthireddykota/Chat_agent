from azure_clients.embedding_client import get_embedding_client
import os

client=get_embedding_client()

def generate_embeddings(chunks):
    response=client.embeddings.create(
        model=os.getenv("EMBEDDING_MODEL"),
        input=chunks
    )
    return [item.embedding for item in response.data]

