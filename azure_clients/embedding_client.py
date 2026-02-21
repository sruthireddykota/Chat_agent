from openai import AzureOpenAI
import streamlit as st


def get_embedding_client():
    client=AzureOpenAI(
        api_key=st.secrets["EMBEDDING_API_KEY"],
        azure_endpoint=st.secrets["EMBEDDING_ENDPOINT"],
        api_version="2024-02-15-preview"
    )
    return client