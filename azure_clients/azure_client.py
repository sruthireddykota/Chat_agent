from agent_framework.azure import AzureOpenAIChatClient
import streamlit as st

def get_client():
    client=AzureOpenAIChatClient(
        endpoint=st.secrets["AZURE_OPENAI_ENDPOINT"],
        deployment_name=st.secrets["AZURE_OPENAI_DEPLOYMENT"],
        api_key=st.secrets["AZURE_OPENAI_API_KEY"]
    )
    return client
    