import hashlib
import json
from typing import Dict, List
from app.utils.logger import get_logger
from app.utils.tools import mcp_web_search, hf_search, academic_paper_search, _get_history

logger = get_logger()

CACHE_TTL = 3600

_ERROR_PREFIXES = (
    "Error performing web search",
    "Error performing repo search",
    "Error performing papers search",
    "Error performing spaces search",
    "Error performing documentation search",
    "Error fetching repository details",
    "HUGGINGFACE MCP error",
    "Error retrieving chat history",
)


async def _cache_key(tool_name: str, **kwargs) -> str:
    """tool_name + hash of sorted kwargs -> deterministic cache key."""
    normalized = json.dumps(kwargs, sort_keys=True, default=str)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    return f"{tool_name}:{digest}"


async def _is_error_result(result) -> bool:
    """
    Detects whether a tool result represents a swallowed error rather than
    a real answer, so we don't cache transient failures as if they were
    successful responses.
    """
    if isinstance(result, str):
        return result.startswith(_ERROR_PREFIXES)

    if isinstance(result, dict):
        # web_search shapes errors as {"results": "Error performing web search,..."}
        inner = result.get("results")
        if isinstance(inner, str) and inner.startswith(_ERROR_PREFIXES):
            return True

    return False


class ResearcherTools:

    def __init__(self, mcp_manager, redis_manager, session_id: str):
        self.mcp_manager = mcp_manager
        self.redis_manager = redis_manager
        self.session_id = session_id
        self.authorization = None

    async def get_tool_functions(self) -> List:
        """Returns the tool functions for registration with the Agent."""

        async def get_history() -> str:
            return await self._get_history_logic()

        async def web_search(query: str, freshness: str) -> Dict:
            return await self._web_search_logic(query, freshness)

        async def repo_search(query: str) -> str:
            """Search Hugging Face for models, datasets, and Spaces repositories.
            Args:
                query: The search query string describing what to look for
            Returns:
                String containing matching repository results
            """
            return await self._repo_search_logic(query)

        async def papers_search(query: str) -> str:
            """Search for ML/AI research papers on Hugging Face.
            Args:
                query: The search query string, e.g. a topic or paper title
            Returns:
                String containing matching paper results
            """
            return await self._papers_search_logic(query)

        async def spaces_search(query: str) -> str:
            """Search Hugging Face Spaces for AI application demos.
            Args:
                query: The search query string describing the type of Space to find
            Returns:
                String containing matching Spaces results
            """
            return await self._spaces_search_logic(query)

        async def documentation_search(query: str, product: str) -> str:
            """Search Hugging Face documentation.
            Args:
                query: The search query string
                product: The Hugging Face product/library the docs relate to
            Returns:
                String containing matching documentation results
            """
            return await self._documentation_search_logic(query, product)

        async def repository_details(repo_ids: List[str]) -> str:
            return await self._repository_details_logic(repo_ids)

        return [
            get_history,
            web_search,
            repo_search,
            papers_search,
            spaces_search,
            documentation_search,
            repository_details,
        ]

    async def _cached_call(self, cache_key: str, call_func):
        cached = await self.redis_manager.get(cache_key)
        if cached is not None:
            logger.info(f'[Researcher Tools] cache hit key={cache_key}')
            return cached

        result = await call_func()

        if await _is_error_result(result):
            logger.warning(f'[Researcher Tools] not caching error result key={cache_key}')
            return result

        await self.redis_manager.put(cache_key, result, ttl=CACHE_TTL, use_content_hash=False)
        return result

    async def _get_history_logic(self) -> str:
        return await _get_history(
            mcp_client=self.mcp_manager.mcp_fastmcp_client,
            session_id=self.session_id,
            authorization=self.authorization,
        )

    async def _web_search_logic(self, query: str, freshness: str) -> Dict:
        key = await _cache_key("web_search", query=query, freshness=freshness)
        try:
            return await self._cached_call(
                key,
                lambda: mcp_web_search(query=query, freshness=freshness, mcp_client=self.mcp_manager.mcp_websearch_client),
            )
        except Exception as e:
            logger.error(f'[Researcher Tools] error in web_search: {e}', exc_info=True)
            return {"results": f"Error performing web search,error: {str(e)}"}

    async def _repo_search_logic(self, query: str) -> str:
        key = await _cache_key("repo_search", query=query)
        try:
            return await self._cached_call(
                key,
                lambda: hf_search(mcp_client=self.mcp_manager.mcp_huggingface_client, tool_name="hub_repo_search", query=query),
            )
        except Exception as e:
            logger.error(f'[Researcher Tools] error in repo_search: {e}', exc_info=True)
            return f"Error performing repo search,error: {str(e)}"

    async def _papers_search_logic(self, query: str) -> str:
        key = await _cache_key("papers_search", query=query)
        try:
            return await self._cached_call(
                key,
                lambda: academic_paper_search(query=query, limit=10),
            )
        except Exception as e:
            logger.error(f'[Researcher Tools] error in papers_search: {e}', exc_info=True)
            return f"Error performing papers search,error: {str(e)}"

    async def _spaces_search_logic(self, query: str) -> str:
        key = await _cache_key("spaces_search", query=query)
        try:
            return await self._cached_call(
                key,
                lambda: hf_search(mcp_client=self.mcp_manager.mcp_huggingface_client, tool_name="space_search", query=query),
            )
        except Exception as e:
            logger.error(f'[Researcher Tools] error in spaces_search: {e}', exc_info=True)
            return f"Error performing spaces search,error: {str(e)}"

    async def _documentation_search_logic(self, query: str, product: str) -> str:
        key = await _cache_key("documentation_search", query=query, product=product)
        try:
            return await self._cached_call(
                key,
                lambda: hf_search(mcp_client=self.mcp_manager.mcp_huggingface_client, tool_name="hf_doc_search", query=query),
            )
        except Exception as e:
            logger.error(f'[Researcher Tools] error in documentation_search: {e}', exc_info=True)
            return f"Error performing documentation search,error: {str(e)}"

    async def _repository_details_logic(self, repo_ids: List[str]) -> str:
        try:
            return await hf_search(mcp_client=self.mcp_manager.mcp_huggingface_client, tool_name="hub_repo_details", repo_ids=repo_ids)
        except Exception as e:
            logger.error(f'[Researcher Tools] error in repository_details: {e}', exc_info=True)
            return f"Error fetching repository details,error: {str(e)}"
