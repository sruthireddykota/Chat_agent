from agent_framework import ChatAgent,MCPStreamableHTTPTool,ChatMessage,ChatMessageStore,Role,DataContent
from agent_framework.redis import RedisChatMessageStore
import asyncio
from typing import Dict
import json
from utils.logger import get_logger

logger= get_logger()

class Researcheragent:
    
    def __init__(self):
        from azure_clients.azure_client import get_client
        self.client=get_client()
        self.mcp_client=MCPStreamableHTTPTool(
        name="MCP Tools",
        url="http://localhost:8000/mcp",
        allowed_tools=["brave_web_search"]
    )
        
    async def researcher_agent(self,query,session_id):
        try :
            
            has_files =bool(query.files) if hasattr(query,'files') else False
             
            if has_files:
                
                logger.info(f'[Researcher Agent] Detected Files in Query')
                
                file_data=query.files[0]
                image_data=file_data.type
                store=lambda:ChatMessageStore()
                logger.info(f'[Researcher Agent] ChatMessage Store Initialised')
                message=ChatMessage(
                    role=Role.USER,
                    data=query.text,
                    contents=[DataContent(
                        media_type =image_data,
                        data=file_data 
                    )]
                )
            else:
                logger.info(f'[Researcher Agent] No Files Detected in Query')
                
                store= lambda: RedisChatMessageStore(
                redis_url="redis://localhost:6379",
                thread_id=f"session_{session_id}",
                max_messages=5 
                )
                logger.info(f'[Researcher Agent] Redis Message Store Initialised with thread_id:{f"session_{session_id}"}')
                
                message=ChatMessage(
                    role=Role.USER,
                    text=query.text
                )
            instructions="""
            You are a helpful research agent with access to real-time web search.

        **Your Capabilities:**
        1. Use brave_web_search to find current, up-to-date information
        2. Search Wikipedia for comprehensive background context
        3. Synthesize information from multiple sources
        4. Provide accurate, well-researched answers

        **Guidelines:**
        - Always search for recent information when asked about current events
        - Use Wikipedia for factual, historical, or conceptual background
        - Cite sources by mentioning the website names
        - If multiple searches are needed, do them systematically
        - Summarize findings clearly and concisely
        - For time-sensitive queries, focus on the most recent results

        **Search Strategy:**
        - For current events: Search directly for the topic
        - For technical topics: Search Wikipedia first for context, then recent sources
        - For comparisons: Search each item separately if needed
        - For "latest" or "recent" queries: Use freshness filters when appropriate

        Remember: You have access to current information through web search. Use it!
        """
            async def web_search(query,freshness)->Dict:
                """Search the web using Brave Search API.
            Args:
                query: The search query string
                freshness: Filter by time - 'pd' (past day), 'pw' (past week), 
                        'pm' (past month), 'py' (past year)
            Returns:
                Dictionary containing search results with titles, URLs, and descriptions"""
                await self.mcp_client.connect()
                
                try:
                    logger.info(f'[Researcher Agent] started MCP Tool: web_search')
                    
                    result=await self.mcp_client.call_tool("brave_web_search",query=query,
                                                count=10,freshness=freshness)
                    
                    result=json.loads(result[0].text)
                    
                    logger.info(f'[Researcher Agent] completed MCP Tool: web_search')
                    
                    return result.get("results","")
                finally:
                    await self.mcp_client.close()
                    
            agent=ChatAgent(chat_client=self.client,
                            instructions=instructions,
                            chat_message_store_factory=store,
                            tools=[web_search])
            
            logger.info(f'[Researcher Agent] query started: {query.text[:100]}')
            
            async for event in agent.run_stream(message):
                if hasattr(event, 'text') and event.text:
                    yield event.text
        except Exception as e:
            logger.error(f'[Researcher Agent] error: {e}')
            
    

def researcher_executor(query, session_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async_gen = Researcheragent().researcher_agent(query, session_id)
    
    logger.info(f'[Researcher Agent] query received: {query.text[:100],session_id}')

    try:
        while True:
            chunk = loop.run_until_complete(async_gen.__anext__())
            yield chunk
    except StopAsyncIteration:
        pass
    finally:
        logger.info(f'[Researcher Agent] query completed: {query.text[:100],session_id}')
        loop.close()

    
    