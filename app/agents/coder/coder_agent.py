from pathlib import Path

from agent_framework import Agent, SkillsProvider

from app.agents.base.base_agent import BaseAgent
from app.agents.tools.coder_agent_tools import CoderTools
from app.agents.instructions.coder_agent_instructions import CoderAgentInstructions
from app.utils.logger import get_logger
from app.utils.script_runner import script_runner
from app.models.agents import AgentRequest
from app.models.constants import AgentType

logger = get_logger()

class CoderAgent(BaseAgent):

    def __init__(self, session_id: str, mongodb_storage, azure_client):
        super().__init__(session_id=session_id, allowed_tools=[
            "list_allowed_directories",
            "read_file",
            "read_text_file",
            "read_media_file",
            "read_multiple_files",
            "write_file",
            "edit_file",
            "create_directory",
            "list_directory",
            "list_directory_with_sizes",
            "directory_tree",
            "move_file",
            "search_files",
            "get_file_info",
            "get_history"],mongodb_storage=mongodb_storage,azure_client=azure_client)

        self.base_instructions = CoderAgentInstructions().get_instructions()
        self.coder_tools = CoderTools(
            mcp_manager=self.mcp_manager,
            redis_manager=self.redis_manager,
            session_id=self.session_id,
        )

    async def agentdefinition(self, requestdata: AgentRequest) -> Agent:

        try:
            session_id = requestdata["session_id"]
            query = requestdata["query"]
            user_id = requestdata["user_id"]
            self.coder_tools.authorization = requestdata.get("authorization")
            tools_list = await self.coder_tools.get_tool_functions()

            coder_skills = SkillsProvider.from_paths(
                skill_paths=[Path(__file__).parent.parent / "skills"],
                script_runner=script_runner,
                disable_load_skill_approval=True,
                disable_read_skill_resource_approval=True,
                disable_run_skill_script_approval=True,
            )

            async with self.mcp_manager.mcp_session():

                message = await self.build_message(query=query)

                agent = Agent(
                    name=AgentType.CODER,
                    client=self.client,
                    instructions=self.base_instructions,
                    tools=[
                        self.client.get_code_interpreter_tool(),
                        tools_list,
                    ],
                    context_providers=[coder_skills]
                )

                response = await self.agent_executor.agent_executor(
                    agent=agent, message=message, session_id=session_id
                )

                if response:
                    await self.mongo_message_store(
                        session_id=session_id,
                        response=response,
                        user_id=user_id,
                        query=query,
                        agent_name=AgentType.CODER,
                    )

                return response

        except Exception as e:
            logger.error(f"[Coder Agent] error occurred: {e}", exc_info=True)
            raise

        finally:
            logger.info("[Coder agent] query completed")
