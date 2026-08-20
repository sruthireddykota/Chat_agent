from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import ClientSecretCredential

from app.config.settings import settings


class PatchedFoundryChatClient(FoundryChatClient):

    def __init__(self, *args, credential, **kwargs):
        self.credential = credential

        super().__init__(
            *args,
            credential=credential,
            **kwargs
        )

    async def _prepare_options(self, messages, options):
        run_options = await super()._prepare_options(
            messages,
            options
        )

        include = run_options.get("include")

        if include:
            filtered = [
                item
                for item in include
                if item != "reasoning.encrypted_content"
            ]

            if filtered:
                run_options["include"] = filtered
            else:
                run_options.pop("include", None)

        return run_options

    async def close(self):
        await self.credential.close()

async def get_client() -> PatchedFoundryChatClient:
    credential = ClientSecretCredential(
        tenant_id=settings.AZURE_TENANT_ID,
        client_id=settings.AZURE_CLIENT_ID,
        client_secret=settings.AZURE_CLIENT_SECRET,
    )

    return FoundryChatClient(
        project_endpoint=settings.AZURE_AI_PROJECT_ENDPOINT,
        model=settings.AZURE_OPENAI_DEPLOYMENT,
        credential=credential,
    )
