from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from datetime import datetime

from agent_framework import Message, Content
from app.agents.base.mcp_manager import MCPManager
from app.agents.base.redis_manager import RedisManager
from app.agents.base.agent_executor import AgentExecutor
from app.azure_clients.azure_client import get_client
from app.utils.logger import get_logger
from app.repositeries.mongodb_server import MongoStore
from app.models.constants import Role,AgentType

logger= get_logger()

class BaseAgent(ABC):

    def __init__(self,allowed_tools: Optional[List],session_id: str):

        self.session_id = session_id
        self.allowed_tools = allowed_tools

        self.client= get_client()
    
        self.redis_manager = RedisManager()
        self.agent_executor = AgentExecutor(self.redis_manager)
        
        self.mongodb_storage = MongoStore()
        self.mcp_manager = (
            MCPManager(session_id=session_id, allowed_tools=allowed_tools)
            if allowed_tools is not None
            else None
        )

    def build_message(self, query: Dict) -> Message:
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

            return Message(
                role='user',
                text=query.get("text", ""),
                contents=[
                    Content.from_text(query.get("text", "")),
                    Content.from_data(data=image_data, media_type=image_media_type),
                ],
            )
        logger.info(f'[{self.__class__.__name__}] No Files Detected in Query')
        
        return Message(
            role='user',
            contents=[Content.from_text(query.get("text", ""))],
        )
    

    def _user_message_store(self, session_id: str, response: str, agent_name: AgentType, user_id: str):
        return {
            "session_id": session_id,
            "role": Role.USER,
            "content": response,
            "agent_name": agent_name,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "sources": None,
        }

    def _assistant_message_store(self, session_id: str, response: str, agent_name: AgentType, user_id: str):
        return {
            "session_id": session_id,
            "role": Role.ASSISTANT,
            "content": response,
            "agent_name": agent_name,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "sources": None,
        }
    
    def mongo_message_store(self, session_id, response, query, agent_name, user_id):

        query_text = query.get("text", "") if isinstance(query, dict) else query
        user_message = self._user_message_store(session_id, query_text, agent_name, user_id)
        self.mongodb_storage.save_message(message=user_message)
        

        assistant_message = self._assistant_message_store(session_id, response, agent_name, user_id)
        self.mongodb_storage.save_message(message=assistant_message)


    
    @abstractmethod
    async def agentdefinition(self,requestdata):
        pass

    async def invoke_agent(self, requestdata):
        try:
            return await self.agentdefinition(requestdata)

        except Exception as e:
            raise RuntimeError("Agent invocation failed") from e
