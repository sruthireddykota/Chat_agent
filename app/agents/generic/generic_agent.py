from agent_framework import Agent

from app.agents.base.base_agent import BaseAgent
from app.agents.tools.generic_agent_tools import GenericTools
from app.agents.instructions.generic_agent_instructions import GenericAgentInstructions
from app.utils.logger import get_logger
from app.models.agents import (AgentRequest)
from app.models.constants import (AgentType)

logger = get_logger()

class GenericAgent(BaseAgent):

    def __init__(self, session_id: str, mongodb_storage, azure_client):

        super().__init__(
            session_id=session_id,
            allowed_tools=["get_history"],
            mongodb_storage=mongodb_storage,
            azure_client=azure_client,
        )
        self.instructions = GenericAgentInstructions().get_instructions()
        self.generic_tools = GenericTools(
            mcp_manager=self.mcp_manager,
            session_id=self.session_id,
        )

    async def agentdefinition(self,requestdata:AgentRequest) -> Agent:
        try:
            session_id = requestdata["session_id"]
            query = requestdata["query"]
            user_id = requestdata["user_id"]
            self.generic_tools.authorization = requestdata.get("authorization")
            tools_list = await self.generic_tools.get_tool_functions()

            async with self.mcp_manager.mcp_session():
                history = await self.generic_tools._get_history_logic()
                message = await self.build_message(query=query, history=history)

                agent = Agent(
                    name=AgentType.GENERIC,
                    client=self.client,
                    instructions=self.instructions,
                    tools=tools_list,
                )
                response = await self.agent_executor.agent_executor(
                    agent=agent, message=message, session_id=session_id
                )
                if response:
                    await self.mongo_message_store(
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
