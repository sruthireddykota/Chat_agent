import hashlib
import json
from typing import List
from app.utils.logger import get_logger
from app.utils.tools import _get_history

logger = get_logger()

CACHE_TTL = 3600 


async def _cache_key(tool_name: str, **kwargs) -> str:
    """tool_name + hash of sorted kwargs -> deterministic cache key."""
    normalized = json.dumps(kwargs, sort_keys=True, default=str)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    return f"{tool_name}:{digest}"


class RAGTools:

    def __init__(self, mcp_manager, redis_manager, session_id: str):
        self.mcp_manager = mcp_manager
        self.redis_manager = redis_manager
        self.session_id = session_id
        self.authorization = None
        self.fastmcp_client = mcp_manager.mcp_fastmcp_client
        self.last_context = []

    async def get_tool_functions(self) -> List:

        async def rag_retrieval(query: str) -> str:
            """
Tool: rag_retrieval
Takes a user query and returns top retrieved chunks from the document database.

Args:
    query (str): The query given by the user

Returns:
    str: Top retrieved chunk information
"""
            return await self._rag_retrieval_logic(query)

        async def get_history() -> str:
            """
Tool: get_history
Retrieves the previous conversation history.
"""
            return await self._get_history_logic()

        return [rag_retrieval, get_history]

    async def _rag_retrieval_logic(self, query: str) -> str:
    
        key = await _cache_key("rag_retrieval_v2", query=query)
        cached = await self.redis_manager.get(key)
        if cached is not None:
            logger.info(f'[RAG Tools] cache hit rag_retrieval key={key}')
            if isinstance(cached, dict):
                self.last_context = cached.get("context", [])
                return cached.get("content", "")
        
            self.last_context = []
            return cached

        logger.info(f'[RAG Tools] rag_retrieval called for query={query}')
        try:
            response = await self.fastmcp_client.call_tool("rag_retrieval", query=query)
            result = response[0].text
            json_result = json.loads(result)
            agent_content = json_result["final_response"]
            self.last_context = json_result.get("chunks", [])
            logger.info(f'[RAG Tools] rag_retrieval successful: {len(agent_content)} chars')
        except Exception as e:
            logger.error(f'[RAG Tools] error in rag_retrieval: {e}', exc_info=True)
            return f"Error performing rag retrieval, error: {str(e)}"

        await self.redis_manager.put(
            key,
            {"content": agent_content, "context": self.last_context},
            ttl=CACHE_TTL,
            use_content_hash=False,
        )
        return agent_content

    async def _get_history_logic(self) -> str:
        logger.info(f"[RAG Tools] get_history called for session_id={self.session_id}")

        return await _get_history(
            mcp_client=self.fastmcp_client,
            session_id=self.session_id,
            authorization=self.authorization,
    )
