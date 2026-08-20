from typing import Dict
import json

import httpx

from agent_framework import MCPStreamableHTTPTool
from app.utils.logger import get_logger

logger=get_logger()

async def _get_history(mcp_client, session_id: str, authorization: str | None = None) -> str:
    logger.info(f"[Chat History] MCP tool called for {session_id}")

    try:
        response = await mcp_client.call_tool(
            "get_chat_history",
            session_id=session_id,
            authorization=authorization,
        )
        messages = response[0].text
        logger.info(f"[Chat History] chat history retrieved for session {session_id}, total chars : {len(messages)}")
        return messages


    except Exception as e:
        logger.error(f"[Chat History] error retrieving chat history: {e}", exc_info=True)
        return f"Error retrieving chat history: {str(e)}"

async def mcp_web_search(query: str, freshness: str,mcp_client: MCPStreamableHTTPTool) -> Dict:
    """Search the web using Brave Search API.
    Args:
        query: The search query string
        freshness: Filter by time - 'pd' (past day), 'pw' (past week),
                'pm' (past month), 'py' (past year)
    Returns:
        Dictionary containing search results with titles, URLs, and descriptions
    """
    try:
        logger.info(f'[Researcher Agent] started MCP Tool: web_search')
        result = await mcp_client.call_tool(
            "brave_web_search", query=query, count=10, freshness=freshness
        )
        result = json.loads(result[0].text)
        logger.info(f'[Researcher Agent] completed MCP Tool: web_search')
        return result.get("results", "")
    except Exception as e:
        logger.error(f'[Researcher Agent] error in web_search: {e}', exc_info=True)
        return {"results": f"Error performing web search,error: {str(e)}"}
                
async def hf_search(mcp_client: MCPStreamableHTTPTool, tool_name: str, **kwargs) -> str:
    try:
        logger.info(f"[HF MCP] Tool called: {tool_name} | args: {kwargs}")

        response = await mcp_client.call_tool(
            tool_name,
            **kwargs
        )
        if response and len(response) > 0:
            return response[0].text

        return "No results found"

    except Exception as e:
        logger.error(f"[HUGGINGFACE MCP] error in {tool_name}: {e}", exc_info=True)
        return f"HUGGINGFACE MCP error: {str(e)}"


async def academic_paper_search(query: str, limit: int = 10) -> str:
    """Search academic papers through OpenAlex."""
    try:
        per_page = max(1, min(int(limit), 20))
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                "https://api.openalex.org/works",
                params={
                    "search": query,
                    "per-page": per_page,
                    "mailto": "topanga@ludwitt.com",
                },
            )
            response.raise_for_status()
            payload = response.json()

        papers = []
        for work in payload.get("results", []):
            location = work.get("primary_location") or {}
            source = location.get("source") or {}
            authors = [
                (author.get("author") or {}).get("display_name")
                for author in (work.get("authorships") or [])[:5]
            ]
            papers.append({
                "title": work.get("display_name"),
                "year": work.get("publication_year"),
                "authors": [author for author in authors if author],
                "citations": work.get("cited_by_count", 0),
                "doi": work.get("doi"),
                "open_access": (work.get("open_access") or {}).get("is_oa", False),
                "url": location.get("landing_page_url") or work.get("id"),
                "source": source.get("display_name"),
            })

        return json.dumps({"source": "OpenAlex", "query": query, "papers": papers})
    except Exception as e:
        logger.error(f"[Academic Search] error searching papers: {e}", exc_info=True)
        return f"Error performing papers search,error: {str(e)}"
    
#Coder Agent Tool wrapper

async def call_mcp_tool(mcp_client, tool_name: str, **kwargs) -> str:
    try:
        response = await mcp_client.call_tool(tool_name, **kwargs)
        return response[0].text
    except Exception as e:
        logger.error(f'[{tool_name}] error: {e}', exc_info=True)
        return f"Error in {tool_name}: {str(e)}"
