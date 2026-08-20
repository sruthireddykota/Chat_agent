from app.utils.logger import get_logger
from app.utils.tools import _get_history
from typing import List
logger = get_logger()

class GenericTools:
    def __init__(self, mcp_manager, session_id: str, authorization: str | None = None):
            self.mcp_manager = mcp_manager
            self.session_id = session_id
            self.authorization = authorization
            self.fastmcp_client = mcp_manager.mcp_fastmcp_client

    async def get_tool_functions(self) -> List:
            async def get_history() -> str:
                """
Tool: get_history
Retrieves the previous conversation history.
"""
                return await self._get_history_logic()

            return [get_history]
        
    async def _get_history_logic(self) -> str:
            logger.info(f"[Generic Tools] get_history called for session_id={self.session_id}")

            return await _get_history(
                mcp_client=self.fastmcp_client,
                session_id=self.session_id,
                authorization=self.authorization,
        )
