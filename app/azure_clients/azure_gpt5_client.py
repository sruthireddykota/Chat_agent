from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import DefaultAzureCredential
from app.config.settings import settings

def get_client() -> AzureAIAgentClient:
    credential = DefaultAzureCredential()

    client = AzureAIAgentClient(
        project_endpoint=settings.AZURE_AI_PROJECT_ENDPOINT,
        model_deployment_name=settings.AZURE_OPENAI_DEPLOYMENT,
        credential=credential
    )
    return client