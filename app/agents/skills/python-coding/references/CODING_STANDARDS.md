# Python Coding Standards

## Type Hints
- All function parameters and return types must be annotated
- Use `from __future__ import annotations` for forward references
- Use `Optional[X]` or `X | None` (Python 3.10+) for nullable types
- Use `TypedDict` for structured dicts passed between functions

```python
# Correct
async def fetch_user(user_id: str) -> dict[str, str] | None:
    ...

# Wrong
async def fetch_user(user_id):
    ...
```

## Docstrings
- All public functions, classes, and modules must have docstrings
- Use Google-style docstrings

```python
def validate_query(query: str, max_length: int = 500) -> bool:
    """Validate a search query string.

    Args:
        query: The raw query string from the user.
        max_length: Maximum allowed character length.

    Returns:
        True if valid, False otherwise.

    Raises:
        ValueError: If query is None.
    """
```

## Error Handling
- Never use bare `except:`
- Catch the most specific exception possible
- Always log before re-raising

```python
# Correct
try:
    result = await client.fetch(url)
except httpx.TimeoutException as e:
    logger.error(f"Timeout fetching {url}: {e}")
    raise
except httpx.HTTPStatusError as e:
    logger.error(f"HTTP {e.response.status_code} for {url}")
    raise

# Wrong
try:
    result = await client.fetch(url)
except:
    pass
```

## Async Patterns
- Use `asyncio.gather()` for concurrent independent calls
- Use `asyncio.wait()` when you need partial results or cancellation
- Never call blocking I/O inside async functions — use `asyncio.to_thread()`

```python
# Concurrent fetches
results = await asyncio.gather(
    fetch_user(user_id),
    fetch_permissions(user_id),
    return_exceptions=True
)

# Blocking I/O in async context
content = await asyncio.to_thread(Path("file.txt").read_text)
```

## Naming
- Functions and variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_single_leading_underscore`
- No abbreviations except: `id`, `url`, `db`, `cfg`, `ctx`

## Project Structure
```
module_name/
├── __init__.py        # public API only
├── models.py          # dataclasses / TypedDicts / Pydantic models
├── core.py            # main logic
├── utils.py           # pure helper functions
└── tests/
    ├── __init__.py
    └── test_core.py
```

## Imports
- Standard library first, then third-party, then local — separated by blank lines
- Never use wildcard imports (`from x import *`)
- Prefer absolute imports over relative

```python
import asyncio
import json
from pathlib import Path

import httpx
from pydantic import BaseModel

from mymodule.models import UserRecord
```

## General Rules
- Max line length: 100 characters
- Max function length: 100 lines — split if longer
- Max file length: 400 lines — split into modules if longer
- No mutable default arguments (`def f(x=[])` is forbidden)
- Use `dataclasses` or `pydantic` for structured data, not plain dicts