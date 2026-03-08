from agent_framework.azure import AzureOpenAIChatClient
from dotenv import load_dotenv
import os
load_dotenv()

def get_client():
    client=AzureOpenAIChatClient(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY")
    )
    return client
    