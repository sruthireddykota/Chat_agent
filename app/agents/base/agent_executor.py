from __future__ import annotations
from agent_framework import Message, Agent


class AgentExecutor():

    def __init__(self, redis_manager):
        self.redis_manager = redis_manager

    async def agent_executor(self, agent: Agent, message: Message, session_id: str):
        full_response = ""
        channel_id = f"redis_{session_id}"

        try:
            async for update in agent.run(messages=message, stream=True):
                if update.text:
                    full_response += update.text
                    chunk_message = {"type": "chunk", "message": update.text}
                    await self.redis_manager.publish_message(channel=channel_id, streamdata=chunk_message)

            await self.redis_manager.publish_message(channel=channel_id, streamdata={"type": "completed"})

        except Exception as e:
            await self.redis_manager.publish_message(
                channel=channel_id, streamdata={"type": "error", "message": str(e)}
            )
            raise

        return full_response