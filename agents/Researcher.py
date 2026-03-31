import asyncio
import json

from pathlib import Path
from typing import Dict
from agent_framework_redis import RedisHistoryProvider
from agent_framework import Agent, MCPStreamableHTTPTool, Message, Content, SkillsProvider

from utils.logger import get_logger
from utils.script_runner import script_runner
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


                message = Message(
                    role='user',
                    text=query.get("text", ""),
                    contents=[
                        Content.from_text(query.get("text", "")),
                        Content.from_data(data=image_data, media_type=image_media_type)
                    ]
                )
            else:
                logger.info(f'[Researcher Agent] No Files Detected in Query')

                message = Message(
                    role='user',
                    contents=[Content.from_text(query.get("text", ""))]
                )
            instructions = """
You are a helpful research agent with access to real-time web search and academic literature.

**Research strategy:**
- For current events or news: prioritize web search
- For scientific or technical topics: use both web search and academic sources
- For literature reviews: use academic sources first, web search to fill gaps
- Always structure your final output using the output formatting skill — load it last

**How to use academic-research skill:**
- To search papers by topic:
  run_skill_script('academic-research', 'scripts/scholar-search.py',
  args={'command': 'search', 'query': '<topic>', 'limit': '5'})

- To look up by DOI:
  run_skill_script('academic-research', 'scripts/scholar-search.py',
  args={'command': 'doi', 'query': '<doi>'})

- To search by author:
  run_skill_script('academic-research', 'scripts/scholar-search.py',
  args={'command': 'author', 'query': '<author name>', 'limit': '5'})

- To get citation chain, always use the DOI returned from the search result:
  run_skill_script('academic-research', 'scripts/scholar-search.py',
  args={'command': 'citations', 'query': '<doi-from-search-result>', 'direction': 'both'})

- To do a full literature review:
  run_skill_script('academic-research', 'scripts/literature-review.py',
  args={'query': '<topic>', 'papers': '20'})

**How to use research-brief skill:**
- First call: read_skill_resource('research-brief/references/BRIEF_FORMAT.md')
- Then format your findings following that schema exactly
- Always load research-brief LAST after all research is complete

**Guidelines:**
- Always use both web search AND academic-research for scientific or technical topics
- Never guess a DOI — always use the DOI returned from a search result
- Never produce final output without loading research-brief last
- If one source returns no results, fall back to the other and note the gap
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
            
            research_skills = SkillsProvider(
                skill_paths=Path(__file__).parent.parent / "skills",
                script_runner=script_runner,
            )
        
            redis_cache=RedisHistoryProvider(redis_url=settings.REDIS_URL, 
                                            source_id=session_id,
                                            max_messages=8)

            agent = Agent(
                client=self.client,
                instructions=instructions,
                tools=[web_search],
                context_providers=[research_skills,redis_cache],
                default_options={
                    'temperature':0.2,
                    'top_p':0.9,
                    'max_tokens':1500
                }
            )

            logger.info(f'[Researcher Agent] query started: {query.get("text", "")[:100]}')
            async for event in agent.run(message,stream=True):
                if event.text:
                    yield event.text
                        

        except Exception as e:
            logger.error(f'[Researcher Agent] error: {e}', exc_info=True)
            import traceback
            traceback.print_exc()  # prints full stack to terminal
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
