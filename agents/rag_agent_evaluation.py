from agent_framework import ChatAgent,MCPStreamableHTTPTool ,ChatMessage ,Role
from azure_clients.azure_client import get_client
from utils.logger import get_logger
import json
from agent_framework.azure import AzureOpenAIChatClient
from config.settings import settings

    
class RAG_agent:
    
    def __init__(self):
        self.client=get_client()
        self.mcp_tool= MCPStreamableHTTPTool(
            name="mcp_tool",
            url=settings.MCP_URL)
        
        self.context=[]

    async def rag_agent(self,query,session_id):
        logger=get_logger()

        message=ChatMessage(
            role=Role.USER,
            text=query
        )
        
        instructions="""You are a Retrieval Augmented Agent, your job is to provide accurate, citation-backed answers by retrieving relevant documents from the knowledge base 

**Available Tools: **
- rag_retreival(query:str)
- get_history()

Querying & Retrieval — Step-by-step

1. Decide if the query is followup question or new query
    - If followup -> get_history() (if available) + rag_retrieval()
    - If new query -> Call rag_retrieval() Immediately
    
2. If followup question fetch the recent history, if you need additional information to answer the query, call rag_retrive() tool (recommended)
3. If the query is completely new or irrelevant to previous, do not consider the past history into context just answer only from the retrieved documents
4. If the context is irrelevant to the question, answer: "No relevant data found for the query, try again later"

**RULES**

1. Do not use internal Training knowledge for answering the query, only answer from retrieved context(Important)
2. Give the response in markdown format and only in english language
3. Do not invent numbers, citations, sources or claims
4. Generating concise, grounded responses and avoid hallucinations.

**Response Format:**

## Summary
- 1-2 short paragraphs. grounded only in retrieved content.

---

## Supporting Details
- **Point 1:** Short explanation derived from the document. Can use citations when explaining
- **Point 2:** Additional evidence or clarification.  
- **Point 3:** Optional — include tables, figures, or quoted phrases if relevant.

---

## Document Sources
- **Document Name** — *Key phrase or topic*  
  Page: X | Section: Y | Paragraph: Z  

- **Document Name** — *Image / Table / Diagram reference*  
  Image: Fig 2 | Page: 5
  

**Failure & Edge Cases**:
- No results: Do not follow response format and just reply "No relevant data found for the query, try again later"

- Partial results: clearly mark which parts are supported and which are not.

- Tool error: Do not follow response format and just say “No relevant data found for the query, try again later”

- Contradictory sources: present both views and list sources for each; recommend follow-up verification.
"""

        async def rag_retreival(query:str)->str:
            """
            This tool takes a user query and returns top retrived chunks from the document database

            Args:
                query (str): The query given by the user 

            Returns:
                str : This returns top Retrived chunk information 
            """
            await self.mcp_tool.connect()
            logger.info(f'[Rag retreival] MCP tool called for {query}')
            try :
                response = await self.mcp_tool.call_tool("rag_retrive", query=query)
                result = response[0].text
                json_result = json.loads(result)

                agent_content=json_result["final_response"]

                self.context.append(json_result["chunks"] )
                logger.info(f'[Rag retreival] rag_retrieve successful: {len(agent_content)}')
                return agent_content
            
            finally:
                await self.mcp_tool.close()
        
        async def get_history()->str:
            """
            This tool retrieves the previous conversation history
            """
            await self.mcp_tool.connect()
            logger.info(f'[Chat History] MCP tool called for {session_id}')
            try :
                response= await self.mcp_tool.call_tool(
                    "get_chat_history",session_id=session_id
                )
                logger.info(f'[Chat History] chat history successful')
                return response[0].text
            
            finally:
                await self.mcp_tool.close()
            
                  
        agent=ChatAgent(chat_client=self.client,name="RAG AGENT",
                        instructions=instructions,
                        tools=[rag_retreival,get_history])
        
        logger.info(f'[RAG AGENT] query received: {query}')
        
        response_text=""

        async for event in agent.run_stream(message):
            if hasattr(event,'text') and event.text:
                response_text+=event.text
    
        return {
            "query": query,
            "response": response_text,
            "context": self.context
        }

