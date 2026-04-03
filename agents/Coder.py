import asyncio

from pathlib import Path
from typing import Dict
from agent_framework_redis import RedisHistoryProvider
from agent_framework import Agent, Message, Content, SkillsProvider, MCPStdioTool
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
    async def _mcp_session(self,mcp_client:MCPStdioTool):
        try:
            await mcp_client.connect()
            logger.info("[MCP Client]: Initialiazed Successfully")
            yield mcp_client

        finally:
            try:
                await mcp_client.close()
            except Exception as e:
                logger.info("[MCP Client]: Secure close task failed")

    async def coder_agent(self, query: Dict, session_id: str):
        workspace= self._create_workspace(session_id)
        self.mcp_client=self._get_mcp_client(session_id=session_id)
        async with self._mcp_session(mcp_client=self.mcp_client):
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

                redis_cache = RedisHistoryProvider(
                    redis_url=settings.REDIS_URL,
                    source_id=session_id,
                    max_messages=8
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
                            self.mcp_client,
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
                            self.mcp_client,
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
                            self.mcp_client,
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
                            self.mcp_client,
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
                            self.mcp_client,
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
                            self.mcp_client,
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
                            self.mcp_client,
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
                            self.mcp_client,
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
                            self.mcp_client,
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
                            self.mcp_client,
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
                            self.mcp_client,
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
                            self.mcp_client,
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
                            self.mcp_client,
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
                            self.mcp_client,
                            "list_allowed_directories"
                        )
                        return response
                    except Exception as e:
                        logger.error(f'[list_allowed_directories] error: {e}', exc_info=True)
                        return f"Error listing allowed directories: {str(e)}"

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
                         ],
                    context_providers=[coder_skills, redis_cache],
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
        
    def _get_mcp_client(self,session_id:str):
        workspace = self._create_workspace(session_id)
        logger.info(f"[Coder Agent] Using workspace: {workspace}")

        fs_client = MCPStdioTool(
            name="filesystem",
            command="npx",
            load_prompts=False,
            cwd=workspace,
            args=[
                "@modelcontextprotocol/server-filesystem",
                workspace 
            ],
        )
        return fs_client

    def _get_instructions(self):
        instructions = """
You are a helpful coding agent specializing in Python and SQL.
You fix bugs, review code, and produce output that is deployed directly — quality is critical.

You have access to a filesystem workspace for reading/writing code.

**MANDATORY RULE**
- Always create files before you generate the code, do not skip this step, if you skip then you Fail 
---

**FILESYSTEM RULES (STRICT - MUST FOLLOW)**
- You can ONLY access files inside: {workspace}
- This is your isolated workspace
- NEVER attempt to access parent directories (../)
- NEVER access system paths (/etc, /root, /app, etc.)
- NEVER modify files outside your workspace
- Always create files inside this workspace when needed

---

**PROJECT STRUCTURE RULES (CRITICAL)**

- All Python code MUST go inside "src/"
- All tests MUST go inside "tests/"
- Always create directories before writing files
- Always generate:
  - main module
  - test file
  - requirements.txt
  - README.md

Example:
- src/moving_averages.py
- tests/test_moving_averages.py

---

**CRITICAL RULE 1: How to use skills (ALL MUST FOLLOW):**

- Call load_skill('skill-name') to get full instructions before any coding task
- Call read_skill_resource('skill-name/references/file.md') to read standards and patterns
- Call run_skill_script('skill-name', 'scripts/script-name.py', args={}) to run checks
- Always use the provided templates for writing new code or tests
- NEVER skip validation


**CRITICAL RUlE 2: FILE WRITING RULES:**
- ALWAYS use relative paths when calling write_file
- Example: "main.py", "utils/helper.py"
- NEVER use absolute paths like /Users/... or /root/...
- NEVER include workspace path in the filename
- The workspace root is already set — do NOT repeat it

Valid:
  path="moving_averages.py"
  path="src/moving_averages.py"

Invalid:
  path="/Users/.../moving_averages.py"
  path="./workspace/filemanager/moving_averages.py"

**CRITICAL RUlE 3:** 
- Always use provided skills and never write code without them. They contain essential standards and checks. -> No Exceptions -> If not followed you have failed.

**How to use python-coding skill:**

For writing new Python code:
  1. load_skill('python-coding')
  2. read_skill_resource('python-coding/references/CODING_STANDARDS.md')
  3. read_skill_resource('python-coding/assets/module-template.py')
  4. Write code following the standards exactly

For debugging Python errors — provide traceback as input:
  run_skill_script('python-coding', 'scripts/analyze_traceback.py',
  args={'input': '<paste traceback here>'})

For reviewing Python code — provide code as input:
  run_skill_script('python-coding', 'scripts/lint_check.py',
  args={'input': '<paste code here>'})

For generating tests:
  1. read_skill_resource('python-coding/references/TEST_STANDARDS.md')
  2. read_skill_resource('python-coding/assets/test-template.py')
  3. Generate tests covering happy path, edge cases, and error cases
**How to use sql-coding skill:**

For writing new SQL queries:
  1. load_skill('sql-coding')
  2. read_skill_resource('sql-coding/references/SQL_STANDARDS.md')
  3. read_skill_resource('sql-coding/references/QUERY_PATTERNS.md')
  4. Write the query following standards
  5. Validate by passing the query directly as input string:
     run_skill_script('sql-coding', 'scripts/validate_query.py',
     args={'input': '<your complete sql query as a single string>'})
  6. If validation returns MUST FIX issues, fix them and re-validate
  7. Only return the query after validation passes

For debugging SQL errors:
  1. read_skill_resource('sql-coding/references/ERROR_PATTERNS.md')
  2. run_skill_script('sql-coding', 'scripts/validate_query.py',
     args={'input': '<paste the broken sql here as a single string>'})

For optimizing slow queries:
  1. read_skill_resource('sql-coding/references/OPTIMIZATION.md')
  2. Analyze query structure and return optimized version with index recommendations

For schema design or migrations:
  1. read_skill_resource('sql-coding/references/SCHEMA_STANDARDS.md')
  2. read_skill_resource('sql-coding/assets/migration-template.sql')
  3. Return CREATE TABLE statements and migration script

**Important — passing input to scripts:**
- The 'input' key in args must contain the actual content as a plain string
- Pass the full SQL or traceback text directly — do not use file paths or placeholders
- Newlines in the string are fine — pass the query exactly as written
- Example: args={'input': 'select id from users where deleted_at = null'}

**Response structure:**
1. Summary — what you did and why
2. Script output — if you ran a skill script, show its output
3. Solution — fixed or new code in fenced blocks
4. Issues found — severity grouped: Must fix / Should fix / Consider
5. Next steps — what to do after applying this fix

**Critical rules:**
- Always load the relevant skill before writing or reviewing any code
- Always pass actual code/SQL content in the 'input' arg — never placeholders
- Run validate_query.py or lint_check.py AFTER generating the code, 
  passing the generated code as the input value
- Never call a validation script before the code exists
- Never return code that has MUST FIX issues from the linter
- Code goes directly to deployment — do not skip quality checks
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
