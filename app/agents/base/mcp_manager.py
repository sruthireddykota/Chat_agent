from agent_framework import MCPStdioTool, MCPStreamableHTTPTool
from typing import Optional, Dict, List
import os

from contextlib import asynccontextmanager
from app.utils.logger import get_logger
from app.config.settings import settings as app_settings
logger = get_logger()


class MCPManager:

    TOOL_TO_SERVER = {
        # filesystem (CoderAgent)
        "list_allowed_directories": "filesystem",
        "read_file": "filesystem",
        "read_text_file": "filesystem",
        "read_media_file": "filesystem",
        "read_multiple_files": "filesystem",
        "write_file": "filesystem",
        "edit_file": "filesystem",
        "create_directory": "filesystem",
        "list_directory": "filesystem",
        "list_directory_with_sizes": "filesystem",
        "directory_tree": "filesystem",
        "move_file": "filesystem",
        "search_files": "filesystem",
        "get_file_info": "filesystem",


        # websearch (ResearcherAgent)
        "web_search": "websearch",
        "brave_web_search": "websearch",

        # huggingface (ResearcherAgent)
        "repo_search": ("huggingface", "hub_repo_search"),
        "papers_search": ("huggingface", "paper_search"),
        "spaces_search": ("huggingface", "space_search"),
        "documentation_search": ("huggingface", "hf_doc_search"),
        "repository_details": ("huggingface", "hub_repo_details"),

        # rag (RAGAgent)
        "rag_retreival": "mcp_tool",
        "mcp_tool": "mcp_tool",
        "get_history": "mcp_tool"
    }

    def __init__(self, session_id: str, allowed_tools=None):
        self.settings = app_settings
        self.session_id = session_id
        self.allowed_tools: List[str] = allowed_tools or []
        allowed_set = set(self.allowed_tools)

        needs_filesystem = any(
            self.TOOL_TO_SERVER.get(t) == "filesystem" for t in allowed_set
        )
        # Filesystem access does not require the optional shell MCP server.
        # The shell package can terminate during MCP initialization, which
        # would otherwise prevent all Coder requests from starting.
        needs_shell = "shell" in allowed_set
        needs_workspace = needs_filesystem or needs_shell

        self.create_workspace = self._create_workspace(session_id) if needs_workspace else None

        self.mcp_filesystem_client = (
            self._get_mcp_filesystem_client(session_id) if needs_filesystem else None
        )
        self.mcp_shell_client = (
            self._get_mcp_shell_client(session_id) if needs_shell else None
        )
        self.mcp_fastmcp_client = (
            self._get_mcp_fastmcp_client(session_id)
            if any(self.TOOL_TO_SERVER.get(t) == "mcp_tool" for t in allowed_set)
            else None
        )
        self.mcp_websearch_client = (
            self._get_mcp_websearch_client()
            if any(self.TOOL_TO_SERVER.get(t) == "websearch" for t in allowed_set)
            else None
        )

        hf_tools_requested = [
            self.TOOL_TO_SERVER[t][1] for t in allowed_set
            if isinstance(self.TOOL_TO_SERVER.get(t), tuple) and self.TOOL_TO_SERVER[t][0] == "huggingface"
        ]
        self.mcp_huggingface_client = (
            self._get_mcp_huggingface_client(hf_tools_requested) if hf_tools_requested else None
        )

    @asynccontextmanager
    async def mcp_session(self):
        clients = [c for c in (
            self.mcp_filesystem_client,
            self.mcp_shell_client,
            self.mcp_fastmcp_client,
            self.mcp_websearch_client,
            self.mcp_huggingface_client,
        ) if c is not None]
        try:
            logger.info(f"[MCP Manager] Starting MCP session for session_id: {self.session_id}")
            for client in clients:
                await client.connect()
            yield
            logger.info(f"[MCP Manager] MCP session completed for session_id: {self.session_id}")
        except Exception as e:
            logger.error(f"[MCP Manager] Error during MCP session for session_id: {self.session_id}: {e}")
            raise
        finally:
            for client in clients:
                await client.close()
            logger.info(f"[MCP Manager] MCP session closed for session_id: {self.session_id}")

    def _create_workspace(self, session_id: str) -> str:
        """
        Create isolated workspace
        """
        base_path = self.settings.CODER_BASE_PATH
        session_path = os.path.join(base_path, session_id)

        os.makedirs(session_path, exist_ok=True)
        return session_path

    def _get_mcp_filesystem_client(self, session_id: str) -> MCPStdioTool:
        workspace = self.create_workspace
        logger.info(f"[Coder Agent] Using workspace: {workspace}")

        return MCPStdioTool(
            name="filesystem",
            command="npx",
            load_prompts=False,
            cwd=workspace,
            args=[
                "-y",
                "@modelcontextprotocol/server-filesystem",
                workspace
            ],
        )

    def _get_mcp_shell_client(self, session_id: str) -> MCPStdioTool:
        workspace = self.create_workspace
        logger.info(f"[Coder Agent] Using workspace: {workspace}")

        return MCPStdioTool(
            name="shell",
            command="npx",
            cwd=workspace,
            load_prompts=False,
            args=[
                "-y",
                "@mako10k/mcp-shell-server@2.1.8"
            ],
            env={
                "MCP_SHELL_SECURITY_MODE": "enhanced",
                "MCP_SHELL_ELICITATION": "true",
                "MCP_SHELL_DEFAULT_WORKDIR": workspace,
                "MCP_SHELL_ALLOWED_WORKDIRS": workspace,
                "MCP_SHELL_MAX_EXECUTION_TIME": "300",
                "MCP_SHELL_MAX_MEMORY_MB": "1024",
                "MCP_DISABLED_TOOLS": "process_terminate,delete_execution_outputs",
            },
            description="Secure Shell MCP",
        )

    def _get_mcp_fastmcp_client(self, session_id: str) -> MCPStreamableHTTPTool:
        return MCPStreamableHTTPTool(
            name="mcp_tool",
            url=self.settings.MCP_URL,
            allowed_tools=["rag_retrive", "get_chat_history"],

        )
    
    

    def _get_mcp_huggingface_client(self, hf_tools_requested: List[str]) -> MCPStreamableHTTPTool:
        return MCPStreamableHTTPTool(
            name="hf_mcp",
            url=self.settings.HUGGINGFACE_URL,
            headers={"Authorization": f"Bearer {os.getenv('HF_TOKEN')}"},
            allowed_tools=hf_tools_requested,
            additional_tool_argument_names={
            "paper_search": ["query"],
            "space_search": ["query"],
            "hf_doc_search": ["query"],
        },
        )
    def _get_mcp_websearch_client(self) -> MCPStreamableHTTPTool:
        return MCPStreamableHTTPTool(
            name="MCP Tools",
            url=self.settings.MCP_URL,
            allowed_tools=["brave_web_search"],
        )
