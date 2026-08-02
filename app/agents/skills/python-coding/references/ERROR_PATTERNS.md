# Python Error Patterns

Quick reference for classifying and fixing common Python errors.
Used by the agent after running analyze_traceback.py.

---

## AttributeError
**Pattern:** `AttributeError: 'NoneType' object has no attribute 'X'`
**Root cause:** A function returned None where an object was expected.
**Fix:** Add a None check before accessing the attribute, or fix the function that returned None.

```python
# Wrong
result = get_user(id)
print(result.name)

# Correct
result = get_user(id)
if result is None:
    raise ValueError(f"User {id} not found")
print(result.name)
```

---

## KeyError
**Pattern:** `KeyError: 'field_name'`
**Root cause:** Accessing a dict key that doesn't exist.
**Fix:** Use `.get()` with a default, or validate the dict shape before access.

```python
# Wrong
name = data["name"]

# Correct
name = data.get("name", "unknown")
# or
if "name" not in data:
    raise ValueError("Missing required field: name")
```

---

## TypeError: missing argument
**Pattern:** `TypeError: func() missing N required positional argument(s)`
**Root cause:** Function called with wrong number of arguments.
**Fix:** Check the function signature and call site. Often caused by forgetting `self` or `await`.

---

## RuntimeError: no running event loop
**Pattern:** `RuntimeError: no running event loop`
**Root cause:** Calling `asyncio.run()` inside an already-running async context (common in Jupyter, Streamlit).
**Fix:** Use `await` directly, or use `asyncio.get_event_loop().run_until_complete()` as fallback.

```python
# In Streamlit context
import asyncio
result = asyncio.run(my_async_func())   # Wrong in Streamlit

# Correct
result = await my_async_func()          # if inside async function
```

---

## ImportError / ModuleNotFoundError
**Pattern:** `ModuleNotFoundError: No module named 'X'`
**Root cause:** Package not installed in the active environment.
**Fix:** Check active venv (`which python`), then `pip install X`.

---

## RecursionError
**Pattern:** `RecursionError: maximum recursion depth exceeded`
**Root cause:** Missing base case in recursive function, or circular data structure.
**Fix:** Add or fix the base case. For deep recursion, consider iterative approach.

---

## ValueError: invalid literal
**Pattern:** `ValueError: invalid literal for int() with base 10: 'X'`
**Root cause:** Trying to cast a non-numeric string to int/float.
**Fix:** Validate input before casting.

```python
# Correct
def safe_int(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None
```

---

## asyncio.exceptions.CancelledError
**Pattern:** Task cancelled unexpectedly.
**Root cause:** Parent task cancelled, timeout hit, or explicit cancellation.
**Fix:** Use `asyncio.shield()` for critical sections, handle `CancelledError` explicitly.

---

## Pydantic ValidationError
**Pattern:** `pydantic.error_wrappers.ValidationError`
**Root cause:** Input data doesn't match the model schema.
**Fix:** Log `e.errors()` to see exactly which fields failed and why.

```python
try:
    model = MyModel(**data)
except ValidationError as e:
    logger.error(f"Validation failed: {e.errors()}")
    raise
```