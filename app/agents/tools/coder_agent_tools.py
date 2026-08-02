from typing import List, Optional

from app.utils.tools import ( call_mcp_tool,_get_history )
from app.utils.logger import get_logger

logger = get_logger()


class CoderTools:

    def __init__(self, mcp_manager, redis_manager, session_id: str):
        self.mcp_manager = mcp_manager
        self.redis_manager = redis_manager
        self.session_id = session_id
        self.filesystem_client = mcp_manager.mcp_filesystem_client
        self.fastmcp_client = mcp_manager.mcp_fastmcp_client

    def get_tool_functions(self) -> List:

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
            return await self._list_allowed_directories()

        async def read_file(path: str, tail: Optional[int] = None, head: Optional[int] = None) -> str:
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
            return await self._read_file(path, tail, head)

        async def read_text_file(path: str, tail: Optional[int] = None, head: Optional[int] = None) -> str:
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
            return await self._read_text_file(path, tail, head)

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
            return await self._read_media_file(path)

        async def read_multiple_files(paths: List[str]) -> str:
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
            return await self._read_multiple_files(paths)

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
            return await self._write_file(path, content)

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
            return await self._edit_file(path, edits, dryRun)

        async def create_directory(path: str) -> str:
            """
Tool: create_directory
Use this to create a new folder.

Args:
    path: Directory path

Returns:
    Success or error message
"""
            return await self._create_directory(path)

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
            return await self._list_directory(path, sortBy)

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
            return await self._list_directory_with_sizes(path, sortBy)

        async def directory_tree(path: str, excludePatterns: Optional[List[str]] = None) -> str:
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
            return await self._directory_tree(path, excludePatterns)

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
            return await self._move_file(source, destination)

        async def search_files(path: str, pattern: str, excludePatterns: Optional[List[str]] = None) -> str:
            """
Tool: search_files
Use this to find files matching a pattern.

Use when:
- You don't know exact file location
- You are searching by extension or name

Args:
    path: Directory to search
    pattern: Glob pattern (e.g., "*.py")
    excludePatterns: Patterns to exclude

Returns:
    Matching file paths
"""
            return await self._search_files(path, pattern, excludePatterns)

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
            return await self._get_file_info(path)

        async def get_history() -> str:
            """
Tool: get_history
Use this to retrieve the previous conversation history.
"""
            return await self._get_history()

        return [
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
        ]

    async def _list_allowed_directories(self) -> str:
        logger.info('[list_allowed_directories]')
        return await call_mcp_tool(self.filesystem_client, "list_allowed_directories")

    async def _read_file(self, path: str, tail: Optional[int] = None, head: Optional[int] = None) -> str:
        logger.info(f'[read_file] path={path}')
        return await call_mcp_tool(self.filesystem_client, "read_file", path=path, tail=tail, head=head)

    async def _read_text_file(self, path: str, tail: Optional[int] = None, head: Optional[int] = None) -> str:
        logger.info(f'[read_text_file] path={path}')
        return await call_mcp_tool(self.filesystem_client, "read_text_file", path=path, tail=tail, head=head)

    async def _read_media_file(self, path: str) -> str:
        logger.info(f'[read_media_file] path={path}')
        return await call_mcp_tool(self.filesystem_client, "read_media_file", path=path)

    async def _read_multiple_files(self, paths: List[str]) -> str:
        logger.info(f'[read_multiple_files] paths={paths}')
        return await call_mcp_tool(self.filesystem_client, "read_multiple_files", paths=paths)

    async def _write_file(self, path: str, content: str) -> str:
        logger.info(f'[write_file] path={path}')
        return await call_mcp_tool(self.filesystem_client, "write_file", path=path, content=content)

    async def _edit_file(self, path: str, edits: list, dryRun: bool = False) -> str:
        logger.info(f'[edit_file] path={path}')
        return await call_mcp_tool(self.filesystem_client, "edit_file", path=path, edits=edits, dryRun=dryRun)

    async def _create_directory(self, path: str) -> str:
        logger.info(f'[create_directory] path={path}')
        return await call_mcp_tool(self.filesystem_client, "create_directory", path=path)

    async def _list_directory(self, path: str, sortBy: str = "name") -> str:
        logger.info(f'[list_directory] path={path}')
        return await call_mcp_tool(self.filesystem_client, "list_directory", path=path, sortBy=sortBy)

    async def _list_directory_with_sizes(self, path: str, sortBy: str = "name") -> str:
        logger.info(f'[list_directory_with_sizes] path={path}')
        return await call_mcp_tool(self.filesystem_client, "list_directory_with_sizes", path=path, sortBy=sortBy)

    async def _directory_tree(self, path: str, excludePatterns: Optional[List[str]] = None) -> str:
        logger.info(f'[directory_tree] path={path}')
        return await call_mcp_tool(
            self.filesystem_client, "directory_tree", path=path, excludePatterns=excludePatterns
        )

    async def _move_file(self, source: str, destination: str) -> str:
        logger.info(f'[move_file] {source} -> {destination}')
        return await call_mcp_tool(self.filesystem_client, "move_file", source=source, destination=destination)

    async def _search_files(self, path: str, pattern: str, excludePatterns: Optional[List[str]] = None) -> str:
        logger.info(f'[search_files] path={path}')
        return await call_mcp_tool(
            self.filesystem_client, "search_files", path=path, pattern=pattern, excludePatterns=excludePatterns
        )

    async def _get_file_info(self, path: str) -> str:
        logger.info(f'[get_file_info] path={path}')
        return await call_mcp_tool(self.filesystem_client, "get_file_info", path=path)

    async def _get_history(self) -> str:
        logger.info(f"[Coder Tools] get_history called for session_id={self.session_id}")

        return await _get_history(
            mcp_client=self.fastmcp_client,
            session_id=self.session_id,
        )