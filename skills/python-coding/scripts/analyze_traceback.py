#!/usr/bin/env python3
"""
analyze_traceback.py

Reads a Python traceback from stdin, classifies the error type,
extracts key information, and prints a structured diagnosis.

Usage:
    echo "<traceback text>" | python3 analyze_traceback.py
    python3 analyze_traceback.py < error.txt
"""
import sys
import re


ERROR_PATTERNS = {
    "AttributeError": {
        "category": "Null reference / wrong type",
        "common_cause": "A function returned None where an object was expected, or wrong variable used.",
        "first_check": "Look at the line above the error — what could be None or the wrong type?",
    },
    "KeyError": {
        "category": "Missing dict key",
        "common_cause": "Accessing a dict key that doesn't exist in this context.",
        "first_check": "Use .get() with a default, or check if key exists before accessing.",
    },
    "TypeError": {
        "category": "Wrong argument type or count",
        "common_cause": "Function called with wrong number/type of arguments, or missing await.",
        "first_check": "Check the function signature. Did you forget 'await' on an async call?",
    },
    "ValueError": {
        "category": "Invalid value",
        "common_cause": "Input data doesn't match the expected format or range.",
        "first_check": "Validate input before passing it to the failing function.",
    },
    "ImportError": {
        "category": "Missing module",
        "common_cause": "Package not installed in the active virtual environment.",
        "first_check": "Run: which python — confirm you're in the right venv, then pip install.",
    },
    "ModuleNotFoundError": {
        "category": "Missing module",
        "common_cause": "Package not installed in the active virtual environment.",
        "first_check": "Run: which python — confirm you're in the right venv, then pip install.",
    },
    "RuntimeError": {
        "category": "Runtime failure",
        "common_cause": "Often event loop issues in async code, or framework-specific constraints.",
        "first_check": "If 'no running event loop': you're calling asyncio.run() inside an async context.",
    },
    "RecursionError": {
        "category": "Infinite recursion",
        "common_cause": "Missing or unreachable base case in a recursive function.",
        "first_check": "Find the recursive function and verify the base case is reachable.",
    },
    "IndexError": {
        "category": "List index out of range",
        "common_cause": "Accessing a list position that doesn't exist.",
        "first_check": "Check the list length before accessing by index. Use .get() pattern or guard.",
    },
    "FileNotFoundError": {
        "category": "Missing file",
        "common_cause": "Path doesn't exist, or relative path is wrong for the working directory.",
        "first_check": "Print Path(path).resolve() to see the absolute path being used.",
    },
    "PermissionError": {
        "category": "File permission denied",
        "common_cause": "Process doesn't have read/write access to the file or directory.",
        "first_check": "Check file permissions with ls -la. May need to run with elevated access.",
    },
}


def extract_error_type(traceback_text: str) -> str | None:
    lines = traceback_text.strip().splitlines()
    for line in reversed(lines):
        line = line.strip()
        match = re.match(r'^([A-Za-z][A-Za-z0-9_]*(?:Error|Exception|Warning))\s*:', line)
        if match:
            return match.group(1)
        if ':' in line:
            candidate = line.split(':')[0].strip()
            if re.match(r'^[A-Z][A-Za-z0-9_]+$', candidate) and len(candidate) > 3:
                return candidate
    return None


def extract_failing_line(traceback_text: str) -> str | None:
    lines = traceback_text.strip().splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith('File "') and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line and not next_line.startswith('File "'):
                return next_line
    return None


def extract_file_location(traceback_text: str) -> str | None:
    lines = traceback_text.strip().splitlines()
    file_lines = [l.strip() for l in lines if l.strip().startswith('File "')]
    if file_lines:
        return file_lines[-1]
    return None


def analyze(traceback_text: str) -> None:
    error_type = extract_error_type(traceback_text)
    failing_line = extract_failing_line(traceback_text)
    file_location = extract_file_location(traceback_text)

    print("=" * 60)
    print("TRACEBACK ANALYSIS")
    print("=" * 60)

    if error_type:
        print(f"\nError Type:     {error_type}")
        info = ERROR_PATTERNS.get(error_type)
        if info:
            print(f"Category:       {info['category']}")
            print(f"Common Cause:   {info['common_cause']}")
            print(f"First Check:    {info['first_check']}")
        else:
            print("Category:       Unrecognized error type — read the full traceback carefully.")
    else:
        print("\nError Type:     Could not extract — input may not be a Python traceback.")

    if file_location:
        print(f"\nFailing At:     {file_location}")

    if failing_line:
        print(f"Failing Line:   {failing_line}")

    print("\n" + "=" * 60)
    print("RECOMMENDED ACTIONS")
    print("=" * 60)
    if error_type and error_type in ERROR_PATTERNS:
        print(f"1. {ERROR_PATTERNS[error_type]['first_check']}")
        print("2. Check the full traceback above for the call chain.")
        print("3. Add logging just before the failing line to inspect variable state.")
    else:
        print("1. Read the full traceback from top to bottom — the root cause is usually at the bottom.")
        print("2. Search for the first line mentioning YOUR code (not library code).")
        print("3. Add a print/log statement before that line to inspect variable state.")

    print()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default=None,
                        help="Traceback text to analyze")
    parsed, _ = parser.parse_known_args()

    if parsed.input:
        traceback_text = parsed.input
    elif not sys.stdin.isatty():
        traceback_text = sys.stdin.read()
    else:
        print("Usage: provide --input '<traceback>' or pipe via stdin")
        sys.exit(1)

    analyze(traceback_text)