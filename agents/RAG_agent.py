from agent_framework import ChatAgent,MCPStreamableHTTPTool ,ChatMessage ,Role,DataContent
from azure_clients.azure_client import get_client
import asyncio
from utils.logger import get_logger

class RAG_agent:
    
    def __init__(self):
        self.client=get_client()
        self.mcp_tool= MCPStreamableHTTPTool(
            name="mcp_tool",
            url="http://localhost:8000/mcp")
        
    async def rag_agent(self,query,session_id):
        logger=get_logger()
        
        has_files = bool(query.files) if hasattr(query, 'files') else False
          
        if has_files:
            logger.info(f'[RAG Agent] Detected Files in Query')
            file_data=query.files[0]
            
            file_type=file_data.type
            
            if len(file_data)>0:
                message=ChatMessage(
                    role=Role.USER,
                    text=query.text,
                    contents=[DataContent(data=file_data.read(),media_type=file_type)]
                    )
        else:
            logger.info(f'[RAG Agent] No Files Detected in Query')
            
            message=ChatMessage(
                role=Role.USER,
                text=query.text
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
                response= await self.mcp_tool.call_tool(
                    "rag_retrive",query=query
                )
                response=response[0].text
                logger.info(f'[Rag retreival] rag_retrieve successful: {len(response)}')
                return response
            
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
        
        logger.info(f'[RAG AGENT] query received: {query.text}')
        
        async for event in agent.run_stream(message):
            if hasattr(event,'text') and event.text:
                yield event.text
              
def rag_executor(query,session_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    logger=get_logger()
    logger.info(f'[RAG Executor] query started: {query.text, session_id}')
    async_gen = RAG_agent().rag_agent(query,session_id)
    try:
        while True:
            chunk = loop.run_until_complete(async_gen.__anext__())
            yield chunk
    except StopAsyncIteration:
        pass
    finally:
        logger.info(f'[RAG Executor] query completed: {query.text, session_id}')
        loop.close()
            