from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from datetime import datetime, timezone

from agent_framework import Message, Content
from app.agents.base.mcp_manager import MCPManager
from app.agents.base.redis_manager import RedisManager
from app.agents.base.agent_executor import AgentExecutor

from app.utils.logger import get_logger

from app.models.constants import Role,AgentType

logger = get_logger()

class BaseAgent(ABC):

    def __init__(self,
                 allowed_tools: Optional[List],
                 session_id: str,
                 mongodb_storage,
                 azure_client):

        self.session_id = session_id
        self.allowed_tools = allowed_tools

        self.client = azure_client
    
        self.redis_manager = RedisManager()
        self.agent_executor = AgentExecutor(self.redis_manager)
        
        self.mongodb_storage = mongodb_storage
        self.mcp_manager = (
            MCPManager(session_id=session_id, allowed_tools=allowed_tools)
            if allowed_tools is not None
            else None
        )

    async def build_message(self, query: Dict,history: Optional[str]="") -> Message:
        """
        Builds a Message from a query dict, handling the optional
        file/image attachment case consistently across all agents.
        """
        has_files = bool(query.get("files"))

        if has_files:

            logger.info(f'[{self.__class__.__name__}] Detected Files in Query')
            file_data = query.get("files", [None])[0]

            image_media_type = (
                file_data.get("type") if isinstance(file_data, dict)
                else getattr(file_data, "type", "image/jpeg")
            )
            image_data = (
                file_data.get("data") if isinstance(file_data, dict)
                else getattr(file_data, "data", file_data)
            )
            if history:
                return Message(
                    role='user',
                    contents=[
                        Content.from_text(query.get("text", "")),
                        Content.from_data(data=image_data, media_type=image_media_type),
                        Content.from_text(f"\n Previous Conversation History (Use for Context and User previous conversation context only) : {history}"),
                    ],
                )

            return Message(
                role='user',
                contents=[
                    Content.from_text(query.get("text", "")),
                    Content.from_data(data=image_data, media_type=image_media_type),
                ],
            )
        logger.info(f'[{self.__class__.__name__}] No Files Detected in Query')
        
        if history:
            return Message(
                role='user',
                contents=[
                    Content.from_text(query.get("text", "")),
                    Content.from_text(f"Previous Conversation History : {history}"),
                ],
            )
        return Message(
            role='user',
            contents=[Content.from_text(query.get("text", ""))],
        )
    

    async def _user_message_store(self, session_id: str, response: str, agent_name: AgentType, user_id: str):
        return {
            "session_id": session_id,
            "role": Role.USER,
            "content": response,
            "agent_name": agent_name,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sources": None,
        }

    async def _assistant_message_store(self, session_id: str, response: str, agent_name: AgentType, user_id: str):
        return {
            "session_id": session_id,
            "role": Role.ASSISTANT,
            "content": response,
            "agent_name": agent_name,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sources": None,
        }
    
    async def mongo_message_store(self, session_id, response, query, agent_name, user_id):

        query_text = query.get("text", "") if isinstance(query, dict) else query
        user_message = await self._user_message_store(session_id, query_text, agent_name, user_id)
        await self.mongodb_storage.save_message(message=user_message)
        await self.mongodb_storage.save_conversation_message(message=user_message)
        

        assistant_message = await self._assistant_message_store(session_id, response, agent_name, user_id)
        await self.mongodb_storage.save_message(message=assistant_message)
        await self.mongodb_storage.save_conversation_message(message=assistant_message)


    
    @abstractmethod
    async def agentdefinition(self,requestdata):
        pass

    async def invoke_agent(self, requestdata):
        try:
            return await self.agentdefinition(requestdata)

        except Exception as e:
            raise RuntimeError("Agent invocation failed") from e
