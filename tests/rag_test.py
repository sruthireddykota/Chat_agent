from agent_framework import ChatAgent,MCPStreamableHTTPTool
from azure_clients.azure_client import get_client
import asyncio

class RAG_agent:
    
    def __init__(self):
        self.client=get_client()
        self.mcp_tool= MCPStreamableHTTPTool(
            name="mcp_tool",
            url="http://localhost:8000/mcp",
    )
        
    
    async def rag_agent(self,query):
        
        instructions="""
**Purpose**
Provide accurate, citation-backed answers by retrieving relevant documents from the knowledge base and generating concise, grounded responses.
Avoid hallucinations and only use retrieved content when the user's request requires it.

**Tools**

rag_retrieval (MCP tool) — input: query (string).
Output: str with document chunks (text + metadata).

Querying & Retrieval — Step-by-step

1. Decide if the query is followup question or new query
    - If followup -> history(if available) + rag_retrieval()
    - If new query -> Call rag_retrieval() Immediately
    
2. If followup look in the recent history, if you need additional information to answer the query, call rag_retrive() tool (recommended)
3. If the query is completely new or irrelevant to previous, do not consider the past history into context just answer only from the retrieved documents
4. If the context is irrelevant to the question, answer: "No relevant data found for the query, try again later"

**RULES**

1. Do not use internal Training knowledge for answering the query, only answer from retrieved context(Important)
2. Give the response in markdown format and only in english language
3. Do not invent numbers, citations, sources or claims

**Response Format:**

Short answer / summary (1-6 lines) — grounded in retrieved content.

Supporting details — bullets or short paragraphs with provenance.

Document sources/ citations - add few words which are main parts and mention the page number or sections or image details if answer from them.

**Failure & Edge Cases**

No results: reply: “No relevant data found"

Partial results: clearly mark which parts are supported and which are not.

Contradictory sources: present both views and list sources for each; recommend follow-up verification."""

        async def rag_retreival(query:str)->str:
            """
            This tool takes a user query and returns top retrived chunks from the document database

            Args:
                query (str): The query given by the user 

            Returns:
                str : This returns top Retrived chunk information 
            """
            await self.mcp_tool.connect()
            print(f'[Rag retreival] MCP tool called for {query}')
            try :
                response= await self.mcp_tool.call_tool(
                    "rag_retrival",query=query
                )
                return response[0].text
            
            finally:
                await self.mcp_tool.close()
            
                  
        agent=ChatAgent(chat_client=self.client,name="RAG AGENT",instructions=instructions,tools=[rag_retreival])

        # async for event in agent.run_stream(query):
        #     if hasattr(event,'text') and event.text:
        #         yield event.text
        #     else:
        #         str(event.text)
        response=await agent.run(query)
        return response
                
        
if __name__=='__main__':
    import streamlit as st
    st.title("RAG test")
    
    query=st.chat_input("Enter query")
    if query is not None:
        st.write(asyncio.run(RAG_agent().rag_agent(query=query)))
    st.button("Clear")
    
    
    
    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)

    # async_gen = RAG_agent().rag_agent(query)

    # try:
    #     while True:
    #         chunk = loop.run_until_complete(async_gen.__anext__())
    #         st.write(chunk)
    # except StopAsyncIteration:
    #     pass
    # finally:
    #     loop.close()