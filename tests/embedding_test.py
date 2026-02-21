from azure_clients.embedding_client import get_embedding_client
import streamlit as st

client=get_embedding_client()

def generate_embeddings(chunks):
    response=client.embeddings.create(
        model=st.secrets["EMBEDDING_MODEL"],
        input=chunks
    )
    print(len(response.data[0].embedding))
generate_embeddings("How are you?")