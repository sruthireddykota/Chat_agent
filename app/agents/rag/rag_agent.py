from agent_framework import Agent

from app.agents.base.base_agent import BaseAgent
from app.agents.tools.rag_agent_tools import RAGTools
from app.agents.instructions.rag_agent_insturctions import RagAgentInstructions
from app.utils.logger import get_logger
from app.models.agents import AgentRequest

from app.models.constants import (AgentType)

logger = get_logger()


class RAGAgent(BaseAgent):

    def __init__(self, session_id: str):

        super().__init__(session_id=session_id, allowed_tools=["rag_retreival", "get_history"])
        
        self.instructions = RagAgentInstructions.get_instructions()
        self.rag_tools = RAGTools(
            mcp_manager=self.mcp_manager,
            redis_manager=self.redis_manager,
            session_id=self.session_id,
        )

    async def agentdefinition(self, requestdata: AgentRequest) -> Agent:

        try:
            session_id = requestdata["session_id"]
            query = requestdata["query"]
            user_id = requestdata["user_id"]

            agent = Agent(
                name = AgentType.RAG,
                client=self.client,
                instructions=self.instructions,
                tools=self.rag_tools.get_tool_functions()
            )
            message=self.build_message(query=query)
            async with self.mcp_manager.mcp_session():
                self.rag_tools.last_context = []

                response=await self.agent_executor.agent_executor(agent=agent,message=message,session_id=session_id)
              
                if response:
                    self.mongo_message_store(
                        session_id=session_id,
                        response=response,
                        query=query,
                        agent_name=AgentType.RAG,
                        user_id=user_id,
                    )
                return {
                    "response": response,
                    "context": self.rag_tools.last_context or [],
                }
    
        except Exception as e:
            logger.error(f"[RAG Agent] error occurred: {e}", exc_info=True)
            return None

        finally:
            logger.info(f'[RAG agent] query completed')
