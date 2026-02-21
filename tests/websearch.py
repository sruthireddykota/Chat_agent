from agent_framework import MCPStreamableHTTPTool
import asyncio

async def test():
    tools = MCPStreamableHTTPTool(
        name="MCP Tools",
        url="http://localhost:8000/mcp",
        allowed_tools=["brave_web_search"]
    )
    
    await tools.connect()
    try:
        result = await tools.call_tool(
            "brave_web_search",
            query="SpaceX Starship"
        )
        print("Results:", result[0].text)
        
        result2 = await tools.call_tool(
            "brave_web_search",
            query="SpaceX Starship"
        )
        print("Cached?", "cached: true" in result2[0].text)
        
    finally:
        await tools.close()

asyncio.run(test())