from agent_framework import Agent

from app.agents.base.base_agent import BaseAgent
from app.agents.instructions.generic_agent_instructions import GenericAgentInstructions
from app.utils.logger import get_logger
from app.models.agents import (AgentRequest)
from app.models.constants import (Role,AgentType)

logger = get_logger()

class GenericAgent(BaseAgent):

    def __init__(self, session_id: str):

        super().__init__(session_id=session_id, allowed_tools=None)
        self.instructions = GenericAgentInstructions().get_instructions()

    async def agentdefinition(self,requestdata:AgentRequest) -> Agent:
        try:
            session_id = requestdata["session_id"]
            query = requestdata["query"]
            user_id = requestdata["user_id"]

            agent = Agent(
                name=AgentType.GENERIC,
                client=self.client,
                instructions=self.instructions,
            )
            message = self.build_message(query=query)
            response = await self.agent_executor.agent_executor(agent=agent, message=message, session_id=session_id)
            if response:
                self.mongo_message_store(
                    session_id=session_id,
                    response=response,
                    query=query,
                    agent_name=AgentType.GENERIC,
                    user_id=user_id,
                )
            return response
        
        except Exception as e:
            logger.error(f"[Generic Agent] error occurred: {e}", exc_info=True)
            return None

