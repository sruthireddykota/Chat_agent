from typing import Dict
import json

from agent_framework import MCPStreamableHTTPTool
from utils.logger import get_logger

logger=get_logger()

#Researcher Agent Tools
async def _get_history(mcp_client: MCPStreamableHTTPTool, session_id: str) -> str:
    """
    This tool retrieves the previous conversation history
    """
    logger.info(f'[Chat History] MCP tool called for {session_id}')
    try :
        response= await mcp_client.call_tool(
            "get_chat_history",session_id=session_id
        )
        logger.info(f'[Chat History] chat history successful')
        return response[0].text
    
    except Exception as e:
        logger.error(f'[Chat History] error retrieving chat history: {e}', exc_info=True)
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
    
#Coder Agent Tool wrapper

async def call_mcp_tool(mcp_client, tool_name: str, **kwargs) -> str:
    try:
        response = await mcp_client.call_tool(tool_name, **kwargs)
        return response[0].text
    except Exception as e:
        logger.error(f'[{tool_name}] error: {e}', exc_info=True)
        return f"Error in {tool_name}: {str(e)}"