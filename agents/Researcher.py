from agent_framework import ChatAgent, MCPStreamableHTTPTool, ChatMessage, ChatMessageStore, Role, DataContent
from agent_framework.redis import RedisChatMessageStore
import asyncio
from typing import Dict
import json
from utils.logger import get_logger
from config.settings import settings
logger = get_logger()


class ResearcherAgent:

    def __init__(self):
        from azure_clients.azure_client import get_client
        self.client = get_client()
        self.mcp_client = MCPStreamableHTTPTool(
            name="MCP Tools",
            url=settings.MCP_URL,
            allowed_tools=["brave_web_search"]
        )

    async def researcher_agent(self, query: Dict, session_id: str):
        try:
            has_files = bool(query.get("files"))

            if has_files:
                logger.info(f'[Researcher Agent] Detected Files in Query')

                file_data = query.get("files", [None])[0]

                image_media_type = file_data.get("type") if isinstance(file_data, dict) else getattr(file_data, "type", "image/jpeg")
                image_data = file_data.get("data") if isinstance(file_data, dict) else getattr(file_data, "data", file_data)

                store = lambda: ChatMessageStore()
                logger.info(f'[Researcher Agent] ChatMessage Store Initialised')

                message = ChatMessage(
                    role=Role.USER,
                    text=query.get("text", ""),
                    contents=[DataContent(
                        media_type=image_media_type,
                        data=image_data
                    )]
                )
            else:
                logger.info(f'[Researcher Agent] No Files Detected in Query')

                store = lambda: RedisChatMessageStore(
                    redis_url=settings.REDIS_URL,
                    thread_id=f"session_{session_id}",
                    max_messages=5
                )
                logger.info(f'[Researcher Agent] Redis Message Store Initialised with thread_id: session_{session_id}')

                message = ChatMessage(
                    role=Role.USER,
                    text=query.get("text", "")
                )

            instructions = """
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

            async def web_search(query: str, freshness: str) -> Dict:
                """Search the web using Brave Search API.
                Args:
                    query: The search query string
                    freshness: Filter by time - 'pd' (past day), 'pw' (past week),
                            'pm' (past month), 'py' (past year)
                Returns:
                    Dictionary containing search results with titles, URLs, and descriptions
                """
                await self.mcp_client.connect()
                try:
                    logger.info(f'[Researcher Agent] started MCP Tool: web_search')
                    result = await self.mcp_client.call_tool(
                        "brave_web_search", query=query, count=10, freshness=freshness
                    )
                    result = json.loads(result[0].text)
                    logger.info(f'[Researcher Agent] completed MCP Tool: web_search')
                    return result.get("results", "")
                finally:
                    await self.mcp_client.close()

            agent = ChatAgent(
                chat_client=self.client,
                instructions=instructions,
                chat_message_store_factory=store,
                tools=[web_search]
            )

            logger.info(f'[Researcher Agent] query started: {query.get("text", "")[:100]}')
            async for event in agent.run_stream(message):
                if hasattr(event, 'text') and event.text:
                    yield event.text
                elif hasattr(event, "message") and getattr(event.message, "text", None):
                    yield event.message.text    

        except Exception as e:
            logger.error(f'[Researcher Agent] error: {e}', exc_info=True)
            raise e

def researcher_executor(query: Dict, session_id: str):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async_gen = ResearcherAgent().researcher_agent(query, session_id)

    logger.info(f'[Researcher Agent] query received: {query.get("text", "")[:100]}, session_id={session_id}')

    try:
        while True:
            chunk = loop.run_until_complete(async_gen.__anext__())
            yield chunk
    except StopAsyncIteration:
        pass
    finally:
        logger.info(f'[Researcher Agent] query completed: {query.get("text", "")[:100]}, session_id={session_id}')
        loop.close()
