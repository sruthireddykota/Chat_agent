from openai import AzureOpenAI
import streamlit as st


def get_client():
    client = AzureOpenAI(
    azure_endpoint=st.secrets["AZURE_OPENAI_ENDPOINT"],
    api_key=st.secrets["AZURE_GPT4_API_KEY"],
    api_version="2025-01-01-preview")
    return client
