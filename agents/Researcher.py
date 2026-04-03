import asyncio
import os

from pathlib import Path
from typing import Dict
from contextlib import asynccontextmanager
from agent_framework_redis import RedisHistoryProvider
from agent_framework import Agent, MCPStreamableHTTPTool, Message, Content, SkillsProvider

from config.settings import settings
from utils.logger import get_logger
from utils.tools import mcp_web_search, hf_search, _get_history
from utils.script_runner import script_runner

logger = get_logger()

class ResearcherAgent:

    def __init__(self):
        from azure_clients.azure_gpt5_client import get_client
        
        self.client = get_client()
        self.mcp_client = MCPStreamableHTTPTool(
            name="MCP Tools",
            url=settings.MCP_URL,
            allowed_tools=["brave_web_search"]
        )
        self.huggingface_mcp=MCPStreamableHTTPTool(
            name="hf_mcp",
            description="MCP server that provides access to the Hugging Face Hub for searching and retrieving machine learning resources. It enables semantic search over models, datasets, Spaces (AI apps), research papers, and documentation, along with fetching detailed repository information (including README content). Designed for real-time discovery of ML assets and up-to-date technical information.",
            url=settings.HUGGINGFACE_URL,
            headers={"Authorization": f"Bearer {os.getenv('HF_TOKEN')}"},
            allowed_tools=[
                "space_search",
                "paper_search",
                "hub_repo_search",
                "hf_doc_search",
                "hub_repo_details"
            ]
        )

    
    @asynccontextmanager
    async def _mcp_session(self):
        
        try:
            await self.mcp_client.connect()
            await self.huggingface_mcp.connect()
            yield self.mcp_client
        finally:
            try:
                await self.mcp_client.close()
                await self.huggingface_mcp.close()
            except Exception as e:
                logger.error(f'[Researcher Agent] Error closing MCP client: {e}')

    async def researcher_agent(self, query: Dict, session_id: str):
        async with self._mcp_session():
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
    You are an advanced research agent designed to perform accurate, structured, and evidence-based analysis using real-time tools and external knowledge sources.

    ---

    ## Available Tools

    ### Web Search
    - web_search(query: str, freshness: str) -> Dict  
    Use for real-time information, news, trends, and general web content.
    
    ### Get History
    - get_history() -> str
    Use this tool to retrieve the previous conversation history for context awareness and continuity in research.

    **MANDATORY**: Always call get_history at the start of the research process to inform your understanding of the user's needs and previous interactions. Use this information to tailor your research approach and ensure continuity in addressing the user's query effectively.
    ---

    ### Academic Research
    Use the academic-research skill for scholarly and peer-reviewed sources.

    #### Commands:
    - Topic search:
    run_skill_script('academic-research', 'scripts/scholar-search.py',
    args={'command': 'search', 'query': '<topic>', 'limit': '5'})

    - DOI lookup:
    run_skill_script('academic-research', 'scripts/scholar-search.py',
    args={'command': 'doi', 'query': '<doi>'})

    - Author search:
    run_skill_script('academic-research', 'scripts/scholar-search.py',
    args={'command': 'author', 'query': '<author name>', 'limit': '5'})

    - Citation chain:
    run_skill_script('academic-research', 'scripts/scholar-search.py',
    args={'command': 'citations', 'query': '<doi>', 'direction': 'both'})

    - Full literature review:
    run_skill_script('academic-research', 'scripts/literature-review.py',
    args={'query': '<topic>', 'papers': '20'})

    ---

    ### Hugging Face MCP (huggingface_mcp)

    Use this MCP tool to access the :contentReference[oaicite:0]{index=0} ecosystem for ML/AI -specific knowledge.

    #### Capabilities:
    - repo_search → find models, datasets, and Spaces  
    - papers_search → retrieve ML/AI research papers  
    - documentation_search → search Hugging Face docs  
    - spaces_search → discover AI applications  
    - repository_details → fetch detailed repo metadata
    

    #### When to use:
    - Queries related to:
    - machine learning models
    - datasets
    - AI frameworks
    - implementation references
    - Prefer over web search for ML-specific discovery
    - Use alongside academic research for deeper validation

    ---

    ##  Research Strategy

    ### 1. Query Classification
    - News / current events → web_search
    - Scientific / technical → academic-research + web_search
    - Machine learning / AI → hf_mcp + academic-research (+ web_search if needed)
    - Literature review → academic-research first, then hf_mcp/web_search

    ---

    ### 2. Multi-Source Validation
    - Always combine at least **two sources** for technical queries:
    - academic + web  
    - academic + hf_mcp  
    - If one source fails, fallback to others and explicitly note the limitation

    ---

    ### 3. Tool Usage Rules
    - Never guess DOIs — always use returned values
    - Prefer structured tool outputs over internal knowledge
    - Use hf_mcp for:
    - up-to-date model/dataset discovery
    - implementation references
    - Avoid unnecessary tool calls if answer is already well-supported

    ---

    ##  Output Formatting (MANDATORY)

    ### Step 1:
    Load format definition:
    read_skill_resource('research-brief/references/BRIEF_FORMAT.md')

    ### Step 2:
    After completing ALL research, format output strictly using research-brief schema.

    ### Rules:
    - Always load research-brief LAST
    - Never produce final output before formatting
    - Ensure structured, clear, and evidence-backed response

    ---

    ##  Constraints

    - Do not hallucinate facts, citations, or DOIs  
    - Clearly distinguish between:
    - verified findings
    - partial evidence
    - missing data  
    - If no reliable data:
    → respond: "Insufficient data available"

    ---

    ##  Goal

    Produce high-quality, structured, and verifiable research outputs by:
    - combining multiple sources
    - leveraging tools intelligently
    - minimizing hallucination
    - maximizing factual accuracy
    """
                async def get_history()->str:
                    """
                    This tool retrieves the previous conversation history
                    """
                    try:
                        response= await _get_history(mcp_client=self.mcp_client, session_id=session_id)
                        return response
                    except Exception as e:
                        logger.error(f'[Researcher Agent] error retrieving chat history: {e}', exc_info=True)
                        return f"Error retrieving chat history: {str(e)}"


                async def web_search(query: str, freshness: str) -> Dict:
                    """Search the web using Brave Search API.
                    Args:
                        query: The search query string
                        freshness: Filter by time - 'pd' (past day), 'pw' (past week),
                                'pm' (past month), 'py' (past year)
                    Returns:
                        Dictionary containing search results with titles, URLs, and descriptions
                    """
                    try:
                        result =await mcp_web_search(query=query,
                                                freshness=freshness,
                                                mcp_client=self.mcp_client)
                        return result
                    except Exception as e:
                        logger.error(f'[Researcher Agent] error in web_search: {e}', exc_info=True)
                        return {"results": f"Error performing web search,error: {str(e)}"}
                
                async def repo_search(query: str) -> str:
                    """ Search for repositories on Hugging Face Hub using the hf_mcp tool.
                    Args:
                        query: The search query string related to machine learning models, datasets, or Spaces.
                    Returns:
                        String containing search results with relevant repositories from Hugging Face."""
                   
                    try:
                        result=await hf_search(mcp_client=self.huggingface_mcp,
                                           tool_name="hub_repo_search",
                                           query=query)
                        return result
                    except Exception as e:
                        logger.error(f'[Researcher Agent] error in repo_search: {e}', exc_info=True)
                        return f"Error performing repo search,error: {str(e)}"
                
                async def papers_search(query: str) -> str:
                    """ Search for research papers on Hugging Face Hub using the hf_mcp tool.
                    Args:
                        query: The search query string related to machine learning research papers.
                    Returns:
                        String containing search results with relevant research papers from Hugging Face."""
                    
                    try:
                        result=await hf_search(mcp_client=self.huggingface_mcp,
                                           tool_name="paper_search",
                                           query=query)
                        return result
                    except Exception as e:
                        logger.error(f'[Researcher Agent] error in papers_search: {e}', exc_info=True)
                        return f"Error performing papers search,error: {str(e)}"
                
                async def spaces_search(query: str) -> str:
                    """ Search for AI applications (Spaces) on Hugging Face Hub using the hf_mcp tool.
                    Args:
                        query: The search query string related to AI applications or Spaces.
                    Returns:
                        String containing search results with relevant Spaces (AI applications) from Hugging Face."""
                    
                    try:
                        result=await hf_search(mcp_client=self.huggingface_mcp,
                                           tool_name="space_search",
                                           query=query)
                        return result
                    except Exception as e:
                        logger.error(f'[Researcher Agent] error in spaces_search: {e}', exc_info=True)
                        return f"Error performing spaces search,error: {str(e)}"
                    
                
                async def documentation_search(query: str,product:str) -> str:
                    """ Search for documentation on Hugging Face Hub using the hf_mcp tool.
                    Args:
                        query: The search query string related to Hugging Face documentation or technical topics.
                        product: Filter by Product. Supply when known for focused results. Example: 'transformers', 'datasets', 'diffusers', 'spaces', 'accelerate', etc.
                    Returns:
                        String containing search results with relevant documentation from Hugging Face."""
                    
                    try:
                        result=await hf_search(mcp_client=self.huggingface_mcp,
                                           tool_name="hf_doc_search",
                                           query=query)
                        return result
                    except Exception as e:
                        logger.error(f'[Researcher Agent] error in documentation_search: {e}', exc_info=True)
                        return f"Error performing documentation search,error: {str(e)}"
                
                async def repository_details(repo_ids: list[str]) -> str:
                    """Get details for one or more Hugging Face repos (model, dataset, or space)
                    
                    Args:
                        repo_ids (list[str]): Repo IDs in author/name format 
                                            (e.g., openai/gpt-oss-120b)
                    
                    Returns:
                        str: Combined details of the specified repositories.
                    """
                    try:
                        result=await hf_search(mcp_client=self.huggingface_mcp,
                                           tool_name="hub_repo_details",
                                           repo_ids=repo_ids)
                        return result
                    except Exception as e:
                        logger.error(f'[Researcher Agent] error in repository_details: {e}', exc_info=True)
                        return f"Error fetching repository details,error: {str(e)}"
    
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
                    tools = [
                        get_history,
                        web_search,
                        repo_search,
                        papers_search,
                        spaces_search,
                        documentation_search,
                        repository_details,

                    ],
                    context_providers=[research_skills,redis_cache],
                    # default_options={
                    #     'temperature':0.2,
                    #     'top_p':0.9,
                    # }
                )

                logger.info(f'[Researcher Agent] query started: {query.get("text", "")[:100]}')
                async for event in agent.run(message,stream=True):
                    if event.text:
                        yield event.text
                            

            except Exception as e:
                logger.error(f'[Researcher Agent] error: {e}', exc_info=True)
                import traceback
                traceback.print_exc() 
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
