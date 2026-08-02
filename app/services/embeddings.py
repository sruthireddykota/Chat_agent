from app.azure_clients.embedding_client import get_embedding_client
from app.config.settings import settings

client=get_embedding_client()

def generate_embeddings(chunks):
    response=client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=chunks
    )
    return [item.embedding for item in response.data]

