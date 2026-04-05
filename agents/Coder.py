from pathlib import Path
from typing import Dict
import asyncio
import json
from agent_framework import Agent, Message, Content, SkillsProvider, MCPStdioTool,MCPStreamableHTTPTool
from contextlib import asynccontextmanager

from utils.logger import get_logger
from utils.tools import call_mcp_tool
from utils.script_runner import script_runner
from config.settings import settings
import os

logger = get_logger()

class CoderAgent:

    def __init__(self):
        from azure_clients.azure_client import get_client
        self.client = get_client()

    def _create_workspace(self,session_id) -> str:
        """
        Create isolated workspace 
        """
        base_path = settings.CODER_BASE_PATH
        session_path = os.path.join(base_path,session_id)

        os.makedirs(session_path, exist_ok=True)
        return session_path
    
    @asynccontextmanager
    async def _mcp_session(self,
                           mcp_filesystem_client:MCPStdioTool,
                           mcp_shell_client:MCPStdioTool,
                           rag_mcp_client:MCPStreamableHTTPTool):
        try:
            await mcp_filesystem_client.connect()
            await mcp_shell_client.connect()
            await rag_mcp_client.connect()
            logger.info("[MCP Client]: Initialiazed Successfully")
            yield mcp_filesystem_client,mcp_shell_client, rag_mcp_client

        finally:
            try:
                await mcp_filesystem_client.close()
                await mcp_shell_client.close()
                await rag_mcp_client.close()
            except Exception as e:
                logger.info("[MCP Client]: Secure close task failed")

    async def coder_agent(self, query: Dict, session_id: str):
        workspace= self._create_workspace(session_id)
        self.mcp_filesystem_client=self._get_file_mcp_client(session_id=session_id)
        self.mcp_shell_client=self._get_shell_mcp_client(session_id=session_id)
        self.rag_mcp_client=self._get_rag_mcp_client()

        async with self._mcp_session(mcp_filesystem_client=self.mcp_filesystem_client,
                                     mcp_shell_client=self.mcp_shell_client,
                                     rag_mcp_client=self.rag_mcp_client):
            try:

                has_files = bool(query.get("files"))

                if has_files:
                    logger.info(f'[Coder Agent] Detected Files in Query')
                    file_data = query.get("files", [None])[0]
                    image_media_type = file_data.get("type") if isinstance(file_data, dict) else getattr(file_data, "type", "image/jpeg")
                    image_data = file_data.get("data") if isinstance(file_data, dict) else getattr(file_data, "data", file_data)
                    message = Message(
                        role='user',
                        text=query.get("text", ""),
                        contents=[
                            Content.from_text(query.get("text", "")),
                            Content.from_data(data=image_data, media_type=image_media_type)
                        ]
                    )
                else:
                    logger.info(f'[Coder Agent] No Files Detected in Query')
                    message = Message(
                        role='user',
                        contents=[Content.from_text(query.get("text", ""))]
                    )

                instructions=self._get_instructions()

                coder_skills = SkillsProvider(
                    skill_paths=[Path(__file__).parent.parent / "skills"],
                    script_runner=script_runner,
                )

                #Tools declarations
                async def read_file(path: str, tail=None, head=None):
                    """
Tool: read_file
Use this to read file contents from disk.

Use when:
- You need to inspect a file's content
- You want partial content (use head or tail)

Args:
    path: File path to read
    tail: Read last N lines (optional)
    head: Read first N lines (optional)

Returns:
    File content as string
"""        
                    logger.info(f'[read_file] path={path}')
                    try:
                        return await call_mcp_tool(
                            self.mcp_filesystem_client,
                            "read_file",
                            path=path,
                            tail=tail,
                            head=head
                        )
                    except Exception as e:
                        logger.error(f'[read_file] error: {e}', exc_info=True)
                        return f"Read File Tool failed, Error:{e}"
                
                async def read_text_file( path: str, tail: int = None, head: int = None) -> str:
                    """
Tool: read_text_file
Use this to read text-based files (e.g., .txt, .py, .md).

Prefer this over read_file for text files.

Args:
    path: Path to the text file
    tail: Last N lines (optional)
    head: First N lines (optional)

Returns:
    Text content
"""
                    logger.info(f'[read_text_file] path={path}')
                    try:
                        return await call_mcp_tool(
                            self.mcp_filesystem_client,
                            "read_text_file",
                            path=path,
                            tail=tail,
                            head=head
                        )
                    except Exception as e:
                        logger.error(f'[read_text_file] error: {e}', exc_info=True)
                        return f"Error reading text file: {str(e)}"
                
                async def read_media_file(path: str) -> str:
                    """
Tool: read_media_file
Use this to read media files like images or audio.

Use when:
- File is not plain text
- You need encoded or metadata output

Args:
    path: Path to media file

Returns:
    Media content representation
"""

                    logger.info(f'[read_media_file] path={path}')
                    try:
                        return await call_mcp_tool(
                            self.mcp_filesystem_client,
                            "read_media_file",
                            path=path
                        )
                    except Exception as e:
                        logger.error(f'[read_media_file] error: {e}', exc_info=True)
                        return f"Error reading media file: {str(e)}"
                
                async def read_multiple_files(paths: list[str]) -> str:
                    """
Tool: read_multiple_files
Use this to read multiple files at once.

Use when:
- You need combined content from several files

Args:
    paths: List of file paths

Returns:
    Combined file contents
"""

                    logger.info(f'[read_multiple_files] paths={paths}')
                    try:
                        return await call_mcp_tool(
                            self.mcp_filesystem_client,
                            "read_multiple_files",
                            paths=paths
                        )
                    except Exception as e:
                        logger.error(f'[read_multiple_files] error: {e}', exc_info=True)
                        return f"Error reading multiple files: {str(e)}"
                
                async def write_file(path: str, content: str) -> str:
                    """
Tool: write_file
Use this to create or overwrite a file.

Use when:
- You need to save generated content
- You want to update a file completely

Args:
    path: Target file path
    content: Content to write

Returns:
    Success or failure message
"""
                    logger.info(f'[write_file] path={path}')
                    try:
                        return await call_mcp_tool(
                            self.mcp_filesystem_client,
                            "write_file",
                            path=path,
                            content=content
                        )
                    except Exception as e:
                        logger.error(f'[write_file] error: {e}', exc_info=True)
                        return f"Error writing file: {str(e)}"
                
                async def edit_file(path: str, edits: list, dryRun: bool = False) -> str:
                    """
Tool: edit_file
Use this to modify parts of a file without rewriting it completely.

Use when:
- You need targeted text replacements
- You want safe edits (use dryRun first)

Args:
    path: File to edit
    edits: List of {oldText, newText}
    dryRun: Preview changes without applying

Returns:
    Edit result or preview
"""
                    logger.info(f'[edit_file] path={path}')
                    try:
                        return await call_mcp_tool(
                            self.mcp_filesystem_client,
                            "edit_file",
                            path=path,
                            edits=edits,
                            dryRun=dryRun
                        )
                        
                    except Exception as e:
                        logger.error(f'[edit_file] error: {e}', exc_info=True)
                        return f"Error editing file: {str(e)}"
                

                async def create_directory(path: str) -> str:
                    """
Tool: create_directory
Use this to create a new folder.

Args:
    path: Directory path

Returns:
    Success or error message
"""
                    logger.info(f'[create_directory] path={path}')
                    try:
                        response = await call_mcp_tool(
                            self.mcp_filesystem_client,
                            "create_directory",
                            path=path
                        )
                        return response
                    except Exception as e:
                        logger.error(f'[create_directory] error: {e}', exc_info=True)
                        return f"Error creating directory: {str(e)}"
                    
                async def list_directory(path: str, sortBy: str = "name") -> str:
                    """
Tool: list_directory
Use this to view files and folders in a directory.

Use when:
- You need to explore folder contents

Args:
    path: Directory path
    sortBy: "name" or "size"

Returns:
    Directory listing
"""
                    logger.info(f'[list_directory] path={path}')
                    try:
                        response = await call_mcp_tool(
                            self.mcp_filesystem_client,
                            "list_directory",
                            path=path,
                            sortBy=sortBy
                        )
                        return response
                    except Exception as e:
                        logger.error(f'[list_directory] error: {e}', exc_info=True)
                        return f"Error listing directory: {str(e)}"
                
                async def list_directory_with_sizes(path: str, sortBy: str = "name") -> str:
                    """
Tool: list_directory_with_sizes
Use this to list directory contents with file sizes.

Use when:
- File size matters (e.g., logs, large files)

Args:
    path: Directory path
    sortBy: "name" or "size"

Returns:
    Directory listing with sizes
"""
                    logger.info(f'[list_directory_with_sizes] path={path}')
                    try:
                        response = await call_mcp_tool(
                            self.mcp_filesystem_client,
                            "list_directory_with_sizes",
                            path=path,
                            sortBy=sortBy
                        )
                        return response
                    except Exception as e:
                        logger.error(f'[list_directory_with_sizes] error: {e}', exc_info=True)
                        return f"Error listing directory with sizes: {str(e)}"
                
                async def directory_tree(path: str, excludePatterns: list[str] = None) -> str:
                    """
Tool: directory_tree
Use this to get a full tree structure of a directory.

Use when:
- You need a hierarchical view of files

Args:
    path: Root directory
    excludePatterns: Patterns to ignore

Returns:
    Directory tree structure
"""
                    logger.info(f'[directory_tree] path={path}')
                    try:
                        response = await call_mcp_tool(
                            self.mcp_filesystem_client,
                            "directory_tree",
                            path=path,
                            excludePatterns=excludePatterns
                        )
                        return response
                    except Exception as e:
                        logger.error(f'[directory_tree] error: {e}', exc_info=True)
                        return f"Error getting directory tree: {str(e)}"
                
                async def move_file(source: str, destination: str) -> str:
                    """
Tool: move_file
Use this to move or rename files.

Args:
    source: Current file path
    destination: New file path

Returns:
    Success or error message
"""
                    logger.info(f'[move_file] {source} -> {destination}')
                    try:
                        response = await call_mcp_tool(
                            self.mcp_filesystem_client,
                            "move_file",
                            source=source,
                            destination=destination
                        )
                        return response
                    except Exception as e:
                        logger.error(f'[move_file] error: {e}', exc_info=True)
                        return f"Error moving file: {str(e)}"
                
                async def search_files(path: str, pattern: str, excludePatterns: list[str] = None) -> str:
                    """
Tool: search_files
Use this to find files matching a pattern.

Use when:
- You don’t know exact file location
- You are searching by extension or name

Args:
    path: Directory to search
    pattern: Glob pattern (e.g., "*.py")
    excludePatterns: Patterns to exclude

Returns:
    Matching file paths
"""
                    logger.info(f'[search_files] path={path}')
                    try:
                        response = await call_mcp_tool(
                            self.mcp_filesystem_client,
                            "search_files",
                            path=path,
                            pattern=pattern,
                            excludePatterns=excludePatterns
                        )
                        return response
                    except Exception as e:
                        logger.error(f'[search_files] error: {e}', exc_info=True)
                        return f"Error searching files: {str(e)}"


                async def get_file_info(path: str) -> str:
                    """
Tool: get_file_info
Use this to get metadata about a file or directory.

Use when:
- You need file size, type, or timestamps

Args:
    path: File or directory path

Returns:
    File metadata
"""
                    logger.info(f'[get_file_info] path={path}')
                    try:
                        response = await call_mcp_tool(
                            self.mcp_filesystem_client,
                            "get_file_info",
                            path=path
                        )
                        return response
                    except Exception as e:
                        logger.error(f'[get_file_info] error: {e}', exc_info=True)
                        return f"Error getting file info: {str(e)}"


                async def list_allowed_directories() -> str:
                    """
Tool: list_allowed_directories
Use this to check which directories are accessible.

Use when:
- You are unsure about valid paths
- You hit permission errors

Returns:
    List of allowed directories
"""
                    logger.info(f'[list_allowed_directories]')
                    try:
                        response = await call_mcp_tool(
                            self.mcp_filesystem_client,
                            "list_allowed_directories"
                        )
                        return response
                    except Exception as e:
                        logger.error(f'[list_allowed_directories] error: {e}', exc_info=True)
                        return f"Error listing allowed directories: {str(e)}"

                async def get_history()->str:
                    """
                    This tool retrieves the previous conversation history
                    """
                    logger.info(f'[Chat History] MCP tool called for {session_id}')
                    try :
                        response= await self.rag_mcp_client.call_tool(
                            "get_chat_history",session_id=session_id
                        )
                        logger.info(f'[Chat History] chat history successful')
                        messages=response[0].text
                        messages=json.dumps(messages)
                        final_message=f"""**Past History:** Use this history messages to hold the conversation or respond related to past conversations
                        ## Messages: {messages}"""

                        return final_message
                    except Exception as e:
                        logger.info(f'[Chat History] MCP tool failed for {session_id}, error:{e}')
                        return f"Chat History MCP tool failed, try again , error:{e}"
            

                #agent
                agent = Agent(
                    client=self.client,
                    instructions=instructions,
                    tools=[self.client.get_code_interpreter_tool(),
                           list_allowed_directories,
                           read_file,
                           read_text_file,
                           read_media_file,
                           read_multiple_files,
                           write_file,
                           edit_file,
                           create_directory,
                           list_directory,
                           list_directory_with_sizes,
                           directory_tree,
                           move_file,
                           search_files,
                           get_file_info,
                           get_history,
                           self.mcp_shell_client,
                         ],
                    context_providers=[coder_skills],
                    default_options={
                        'temperature': 0.2,
                        'top_p': 0.9,
                    }
                )
                logger.info(f'[Coder Agent] query started: {query.get("text", "")[:100]}')

                async for event in agent.run(message, stream=True):
                    if event.text:
                        yield event.text
                    
            except Exception as e:
                logger.error(f'[Coder Agent] error: {e}', exc_info=True)
                raise e
        
    def _get_file_mcp_client(self,session_id:str):
        workspace = self._create_workspace(session_id)
        logger.info(f"[Coder Agent] Using workspace: {workspace}")

        fs_client = MCPStdioTool(
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
        return fs_client
    
    def _get_rag_mcp_client(self):
        rag_mcp_client= MCPStreamableHTTPTool(
            name="mcp_tool",
            url=settings.MCP_URL)
        return rag_mcp_client
        
    def _get_shell_mcp_client(self,session_id:str):
        workspace = self._create_workspace(session_id)
        logger.info(f"[Coder Agent] Using workspace: {workspace}")

        shell_client=MCPStdioTool(
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
                "MCP_DISABLED_TOOLS": "process_terminate,delete_execution_outputs",},
            description="Secure Shell MCP",

        )
        return shell_client

        

    def _get_instructions(self):
        instructions = """
You are a helpful coding agent specializing in Python and SQL.
You fix bugs, review code, and produce output that is deployed directly — quality is critical.

You have access to:
- A filesystem workspace for reading and writing code
- A shell client for executing commands, running scripts, and installing dependencies
- get_history tool to retrieve past conversation or history
---

**MANDATORY RULE**
- Always create files before you generate the code, do not skip this step, if you skip then you Fail
- Always call get_history tool before you start any task, you need to load past history for better context, do not skip this step, if you skip then you Fail
- Always load code-architecture skill when working on a coding tasks, do not skip this step, if you skip then you Fail
---

## UNIVERSAL SKILL PROTOCOL

This is how you use ANY skill — follow this for every skill you load, no exceptions.

### Step 1 — Load the skill
  load_skill('<skill-name>')
  
  This gives you the skill's SKILL.md file. Read it fully before doing anything else.
  The SKILL.md always contains:
  - ## Skill entry point  →  exact steps to follow in order
  - ## Dependencies       →  what to install and how to check first
  - ## Instructions       →  task-specific workflows (write / debug / review / etc.)
  - ## Output rules       →  mandatory formatting and quality constraints

### Step 2 — Follow the entry point
  Every skill has a ## Skill entry point section.
  Execute those steps in the exact order listed — do not skip or reorder.

### Step 3 — Handle dependencies
  Every skill has a ## Dependencies section.
  If it lists packages:
    a. Check first:  shell → pip show <package>
    b. Skip install if already present
    c. Install only if missing:  shell → uv pip install <package>
    d. Verify:  shell → python -c "import <package>"
  If it says "None" — proceed without any install.

### Step 4 — Identify the task type
  Every skill has a ## Instructions section with subsections per task type.
  Match the user's request to the correct task type (write / debug / review / optimize / etc.)
  Follow that subsection's workflow exactly.

### Step 5 — Read referenced resources
  The workflow will tell you which resources to read.
  Always read them — they contain the standards and templates your output must follow.
  Use: read_skill_resource('<skill-name>/references/<file>')
       read_skill_resource('<skill-name>/assets/<file>')

### Step 6 — Run skill scripts
  The workflow will tell you which scripts to run and when.
  Always run them — never skip validation.
  Use: run_skill_script('<skill-name>', 'scripts/<script>.py', args={'input': '<content>'})
  Pass the actual content as the input value — never a file path or placeholder.

### Step 7 — Fix and re-validate
  If a validation script returns MUST FIX issues:
    - Fix every one of them
    - Re-run the validation script
    - Do not return output until validation is clean

---

**FILESYSTEM RULES (STRICT - MUST FOLLOW)**
- You can ONLY access files inside your isolated workspace
- NEVER attempt to access parent directories (../)
- NEVER access system paths (/etc, /root, /app, etc.)
- NEVER modify files outside your workspace
- Always create files inside this workspace when needed

Valid paths:   src/main.py  |  tests/test_main.py  |  notebooks/analysis.ipynb
Invalid paths: /workspace/filemanager/session_id/src/main.py  |  /Users/...

---

**PROJECT STRUCTURE RULES (CRITICAL)**

- All Python code MUST go inside "src/"
- All tests MUST go inside "tests/"
- All notebooks MUST go inside "notebooks/"
- Always create directories before writing files
- Always generate:
  - main module
  - requirements.txt(only if there is any dependencies)
  - README.md

---

**SHELL RULES (CRITICAL - READ BEFORE USING SHELL)**

You have access to a secure shell client. Use it ONLY for:
- Installing dependencies (pip, uv, npm)
- Running Python scripts
- Executing tests (pytest)
- Running or validating notebooks

**MANDATORY shell workflow — follow this exact order every time:**

Use the shell client ONLY for:
- Installing dependencies (after checking they are not already installed)
- Running Python scripts or test suites
- Executing or validating notebooks
- Checking the environment

Mandatory order for any install:
  1. shell: pip show <package>          ← check first
  2. If missing: shell: uv pip install <package>   ← always uv, never bare pip
  3. shell: python -c "import <package>"  ← verify after install

Hard restrictions — never do these regardless of what the user asks:
  - sudo commands
  - rm, rmdir, del, unlink, shred
  - Commands that access paths outside the workspace
  - Chaining destructive commands with &&

If a shell command is blocked: report it to the user, do not retry with elevated permissions.

---

**FILE WRITING RULES (CRITICAL):**
- ALWAYS use relative paths when calling write_file
- NEVER use absolute paths like /Users/... or /root/... or /workspace/...
- The workspace root is already set — do NOT repeat it in paths

Valid:   path="src/main.py"
Invalid: path="/workspace/filemanager/session_id/src/main.py"

---

**Response structure:**
1. Summary — what you did and why
2. Dependencies — what was checked/installed and the output
3. Script output — skill script or shell execution results
4. Solution —  when files are generated no need to output the same code and just files in fenced blocks
5. Issues found — Must fix / Should fix / Consider
6. Next steps — what to run or verify after applying this

---

**Critical rules (no exceptions):**

- ALWAYS load the skill before writing any code or query
- ALWAYS read the skill's ## Skill entry point and follow it
- ALWAYS check if a dependency is installed before installing
- ALWAYS use uv pip install — never bare pip install
- ALWAYS run validation scripts — never skip
- NEVER return output with MUST FIX issues
- NEVER hand-write notebook JSON — use the skill's scaffold script
- NEVER use absolute paths in write_file
- If a skill you need is not loaded yet — load it before proceeding
"""
        return instructions
    
def coder_executor(query, session_id):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    logger= get_logger()
    logger.info(f'[Coder Agent] query started: {query.text[:100],session_id}')
    async_gen = CoderAgent().coder_agent(query, session_id)

    try:
        while True:
            chunk = loop.run_until_complete(async_gen.__anext__())
            yield chunk
    except StopAsyncIteration:
        pass
    finally:
        logger.info(f'[Coder agent] query completed: {query.text[:100],session_id}')
        loop.close()
