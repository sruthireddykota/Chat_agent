from agent_framework import Agent

from app.models.workflow import WorkflowStep, WorkflowBuilder
from app.azure_clients.azure_client import get_client
from utils.logger import get_logger

logger = get_logger()

class WorkflowBuilderr:
    
    async def _build_instructions(self,instructions,name):
        try :
            final_instructions=""
            if name is not None:
                final_instructions+=f"You are a helpful {name} agent, Your job is help user on the task"
            if instructions is not None:
                final_instructions+= f"User task/Input:\n\n {instructions}"
            return final_instructions
        
        except Exception as e:
            logger.error(f"Step Agent Instruction Building failed, Error:{e}")
    
    async def build_workflow_agents(self, steps: list[WorkflowStep]) -> list:
        try :

            agents = []
            client= await get_client()
            for step in steps:
                agent = Agent(
                    client= client,
                    name=step.name,
                    instructions=await self._build_instructions(instructions=step.instructions, name=step.name)
                )
                agents.append(agent)
            return agents

        except Exception as e:
            logger.error(f"Build workflow Agent failed, Error:{e}")

    async def build_workflow(self, workflow: WorkflowBuilder) :
        try : 
            if workflow.workflow_type == "sequential":
                from agent_framework.orchestrations import SequentialBuilder
                agents = await self.build_workflow_agents(steps = workflow.steps)
                workflow = SequentialBuilder(participants = agents,
                                            chain_only_agent_responses=True).build()

            elif workflow.workflow_type == "concurrent":
                from agent_framework.orchestrations import ConcurrentBuilder
                agents = await self.build_workflow_agents(steps = workflow.steps)
                workflow = ConcurrentBuilder(participants = agents).build()

            elif workflow.workflow_type == "handoff":
                from agent_framework.orchestrations import HandoffBuilder
                agents = await self. build_workflow_agents(steps = workflow.steps)
                workflow = HandoffBuilder(participants= agents).build()

            elif workflow.workflow_type == "groupchat":
                from agent_framework.orchestrations import GroupChatBuilder
                agents = await self.build_workflow_agents(steps= workflow.steps)
                workflow = GroupChatBuilder(participants= agents).build()

            return workflow
    
        except Exception as e :
            logger.error(f"[Workflow Builder] failed {e}")

    