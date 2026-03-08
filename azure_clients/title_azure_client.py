from openai import AzureOpenAI
from dotenv import load_dotenv
import os
load_dotenv()

def get_client():
    client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_GPT4_API_KEY"),
        api_version="2025-01-01-preview"
    )
    return client
