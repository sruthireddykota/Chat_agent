from pathlib import Path

from agent_framework import Agent, SkillsProvider

from app.agents.base.base_agent import BaseAgent
from app.agents.tools.researcher_agent_tools import ResearcherTools
from app.agents.instructions.researcher_agent_instructions import (
    ResearcherAgentInstructions,
)
from app.models.agents import AgentRequest
from app.models.constants import AgentType
from app.utils.logger import get_logger
from app.utils.script_runner import script_runner

logger = get_logger()


class ResearcherAgent(BaseAgent):

    def __init__(self, session_id: str):
        super().__init__(
            session_id=session_id,
            allowed_tools=[
                "get_history",
                "web_search",
                "repo_search",
                "papers_search",
                "spaces_search",
                "documentation_search",
                "repository_details",
            ],
        )

        self.base_instructions = ResearcherAgentInstructions().get_instructions()

        self.researcher_tools = ResearcherTools(
            mcp_manager=self.mcp_manager,
            redis_manager=self.redis_manager,
            session_id=self.session_id,
        )

    async def agentdefinition(self, requestdata: AgentRequest) -> Agent:

        try:
            session_id = requestdata["session_id"]
            query = requestdata["query"]
            user_id = requestdata["user_id"]

            researcher_skills = SkillsProvider.from_paths(
                skill_paths=[Path(__file__).parent.parent / "skills"],
                script_runner=script_runner,
                disable_load_skill_approval=True,
                disable_read_skill_resource_approval=True,
                disable_run_skill_script_approval=True,
            )

            message = self.build_message(query=query)

            async with self.mcp_manager.mcp_session():

                history = await self.researcher_tools._get_history_logic()

                instructions = (
                    f"{self.base_instructions}\n\n"
                    "---\n\n"
                    "## Conversation History (already retrieved, do not call get_history again)\n"
                    f"{history}"
                )

                agent = Agent(
                    name=AgentType.RESEARCHER,
                    client=self.client,
                    instructions=instructions,
                    tools=[
                        *self.researcher_tools.get_tool_functions(),
                    ],
                    context_providers=[researcher_skills]
                )

                response = await self.agent_executor.agent_executor(
                    agent=agent,
                    message=message,
                    session_id=session_id,
                )

                if response:
                    self.mongo_message_store(
                        session_id=session_id,
                        response=response,
                        user_id=user_id,
                        query=query,
                        agent_name=AgentType.RESEARCHER,
                    )
                return response

        except Exception as e:
            logger.error(
                f"[Researcher Agent] error occurred: {e}",
                exc_info=True,
            )

        finally:
            logger.info("[Researcher Agent] query completed")