from agent_framework import MCPStreamableHTTPTool
import asyncio
from typing import Annotated,Dict
import json

mcp_client=MCPStreamableHTTPTool(
        name="MCP Tools",
        url="http://localhost:8000/mcp",
        
    )

async def web_search(query,freshness)->Dict:
        """Search the web using Brave Search API.
    Args:
        query: The search query string
        freshness: Filter by time - 'pd' (past day), 'pw' (past week), 
                   'pm' (past month), 'py' (past year)
    Returns:
        Dictionary containing search results with titles, URLs, and descriptions"""
        await mcp_client.connect()
        try:
            result=await mcp_client.call_tool("brave_web_search",query=query,
                                        count=10,freshness=freshness)
            result=json.loads(result[0].text)
            return result.get("results","")
        finally:
            await mcp_client.close()
            
            
async def retrieve(query):
    await mcp_client.connect()
    try:
        response = await mcp_client.call_tool("rag_retrive", query=query)
        result = response[0].text
        json_result = json.loads(result)

        agent_content=json_result["final_response"]

        return agent_content
            
    finally:
        await mcp_client.close()
        
async def history_retrive(session_id):
    await mcp_client.connect()
    try:
        response= await mcp_client.call_tool("get_chat_history",session_id=session_id)
        return response[0].text
    finally:
        await mcp_client.close()

result=asyncio.run(retrieve(" What are the key rules governing pit stops in Formula 1?"))
print(result)