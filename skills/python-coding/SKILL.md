---
name: python-coding
description: Write, debug, review, and generate tests for Python code following best practices. Use when asked to write Python functions, classes, or modules; fix Python errors or tracebacks; review existing Python code; or generate Python unit tests. Covers async, type hints, error handling, and project structure conventions.
license: MIT
compatibility: Requires python3.10+. Scripts use stdlib only — no pip install needed.
metadata:
  author: agent-framework
  version: "1.0"
---

## Purpose

Produce clean, typed, well-structured Python code that follows consistent conventions.
Handle the full coding lifecycle: write → debug → review → test.

## When to load this skill

Load when:
- Asked to write any Python function, class, module, or script
- Given a Python traceback or error to fix
- Asked to review or improve existing Python code
- Asked to generate unit tests for Python code
- Asked about Python patterns, async, typing, or project structure

## Instructions

### Step 1 — Identify the task type

Determine which of these you are doing:
- **Write** — producing new code from a spec or description
- **Debug** — fixing broken code from an error or traceback
- **Review** — improving existing working code
- **Test** — generating unit tests for existing code

Each has a different workflow below.

---

### Writing new code

1. Load coding standards first:
   `read_skill_resource("python-coding/references/CODING_STANDARDS.md")`

2. Check if a relevant template exists:
   `read_skill_resource("python-coding/assets/module-template.py")`

3. Follow the standards exactly — type hints, docstrings, error handling are mandatory.

4. Structure your output as:
   - The code in a fenced ```python block
   - A short "Usage" example below it
   - Any dependencies the caller needs to install (if any)

---

### Debugging

1. Load the error reference:
   `read_skill_resource("python-coding/references/ERROR_PATTERNS.md")`

2. Run the traceback analyzer on the error:
   `run_skill_script("python-coding/scripts/analyze_traceback.py", input=<traceback text>)`

3. Read the script output — it classifies the error type and suggests root causes.

4. Return:
   - Root cause (one sentence)
   - Fixed code in a fenced ```python block
   - What was wrong and why (2-3 sentences)

---

### Code review

1. Load coding standards:
   `read_skill_resource("python-coding/references/CODING_STANDARDS.md")`

2. Run the linter check:
   `run_skill_script("python-coding/scripts/lint_check.py", input=<code>)`

3. Return feedback grouped by severity:
   - **Must fix** — bugs, missing error handling, type errors
   - **Should fix** — style, naming, missing docstrings
   - **Consider** — structural suggestions, performance

---

### Generating tests

1. Load the test standards:
   `read_skill_resource("python-coding/references/TEST_STANDARDS.md")`

2. Load the test template:
   `read_skill_resource("python-coding/assets/test-template.py")`

3. Generate tests that cover:
   - Happy path
   - Edge cases (empty input, None, zero, max values)
   - Expected exceptions

---

## Output rules

- Always use type hints — no untyped function signatures
- Always include docstrings on public functions and classes
- Never use bare `except:` — always catch specific exceptions
- Prefer `pathlib.Path` over `os.path`
- Async code must use `asyncio` patterns from the standards doc
- Max function length: 100 lines. If longer, suggest splitting.