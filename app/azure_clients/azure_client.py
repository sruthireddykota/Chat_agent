from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import ClientSecretCredential

from app.config.settings import settings


class PatchedFoundryChatClient(FoundryChatClient):
    """
    Works around a library default in agent-framework-openai==1.11.0:
    RawOpenAIChatClient._prepare_options unconditionally appends
    "reasoning.encrypted_content" to `include` whenever the request
    is stateless (no conversation_id/previous_response_id/conversation
    supplied). Non-reasoning model deployments (e.g. gpt-4o) reject this
    with a 400 "Encrypted content is not supported with this model."
    Strip it back out here since we don't use reasoning models.
    """

    async def _prepare_options(self, messages, options):
        run_options = await super()._prepare_options(messages, options)
        include = run_options.get("include")
        if include:
            filtered = [item for item in include if item != "reasoning.encrypted_content"]
            if filtered:
                run_options["include"] = filtered
            else:
                run_options.pop("include", None)
        return run_options


def get_client() -> FoundryChatClient:
    credential = ClientSecretCredential(
        tenant_id=settings.AZURE_TENANT_ID,
        client_id=settings.AZURE_CLIENT_ID,
        client_secret=settings.AZURE_CLIENT_SECRET,
    )

    client = PatchedFoundryChatClient(
        project_endpoint=settings.AZURE_AI_PROJECT_ENDPOINT,
        model=settings.AZURE_OPENAI_DEPLOYMENT,
        credential=credential,
    )
    return client