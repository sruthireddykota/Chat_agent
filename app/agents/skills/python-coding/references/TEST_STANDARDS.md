# Python Test Standards

## Framework
Use `pytest` with `pytest-asyncio` for async tests.

## File Naming
- Test files: `test_<module_name>.py`
- Test functions: `test_<function_name>_<scenario>`

```
test_fetch_user_success
test_fetch_user_not_found
test_fetch_user_timeout
```

## Required Coverage Per Function
Every tested function must have:
1. **Happy path** — normal valid input, expected output
2. **Edge cases** — empty string, None, 0, empty list, max values
3. **Error cases** — expected exceptions are raised correctly

## Async Tests
```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_fetch_user_success():
    result = await fetch_user("user_123")
    assert result is not None
    assert result["id"] == "user_123"
```

## Mocking
Use `unittest.mock.AsyncMock` for async dependencies.

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_fetch_user_calls_api():
    with patch("mymodule.http_client.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {"id": "123", "name": "Alice"}
        result = await fetch_user("123")
        mock_get.assert_called_once_with("/users/123")
```

## Fixtures
Define reusable fixtures in `conftest.py`:

```python
# conftest.py
import pytest

@pytest.fixture
def sample_user() -> dict:
    return {"id": "user_123", "name": "Alice", "email": "alice@example.com"}

@pytest.fixture
async def db_client():
    client = await create_test_db()
    yield client
    await client.close()
```

## Assertions
- Be specific — assert exact values, not just truthiness
- Use `pytest.raises` for exception testing

```python
# Correct
assert result["name"] == "Alice"
assert len(results) == 3

# Wrong
assert result
assert results

# Exception testing
with pytest.raises(ValueError, match="User .* not found"):
    await fetch_user("nonexistent_id")
```

## What NOT to test
- Private methods (`_method`) — test through public interface
- Framework code (httpx, pydantic internals)
- Trivial getters/setters with no logic